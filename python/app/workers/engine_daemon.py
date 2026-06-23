import asyncio
import json
from datetime import datetime, timezone
import sys
import os

# Add build directory to path to import _nanotrade_ext
build_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "build")
)
if build_dir not in sys.path:
    sys.path.append(build_dir)

import _nanotrade_ext
from app.core.config import settings
from app.core.database import supabase
from app.core.logger import setup_logging, get_logger
import redis.asyncio as redis_async
from redis.exceptions import ResponseError

# Initialize logging for the worker
setup_logging(log_level=settings.LOG_LEVEL)
logger = get_logger("engine_daemon")

STREAM_KEY = "engine:orders_stream"
GROUP_NAME = "engine_group"
CONSUMER_NAME = "worker-1"
DLQ_STREAM = "engine:dead_letter_queue"


class EngineDaemon:
    def __init__(self):
        self.redis = redis_async.from_url(settings.REDIS_URL, decode_responses=True)
        self.engine = _nanotrade_ext.MatchingEngine()

    async def init_stream(self):
        try:
            await self.redis.xgroup_create(STREAM_KEY, GROUP_NAME, mkstream=True)
            logger.info(f"Created consumer group {GROUP_NAME} for stream {STREAM_KEY}")
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group {GROUP_NAME} already exists")
            else:
                raise e

    async def hydrate_engine(self):
        """
        Reconstructs the exact order book state from the database.
        """
        logger.info("Hydrating Matching Engine from database...")

        # Revert any stuck PROCESSING orders to QUEUED
        # This handles crash recovery safely
        processing_resp = (
            supabase.table("orders").select("id").eq("status", "PROCESSING").execute()
        )
        if processing_resp.data:
            stuck_ids = [row["id"] for row in processing_resp.data]
            logger.warning(
                f"Found {len(stuck_ids)} orders stuck in PROCESSING. Reverting to QUEUED."
            )
            for oid in stuck_ids:
                supabase.table("orders").update({"status": "QUEUED"}).eq(
                    "id", oid
                ).execute()

        # Fetch active orders to rebuild the book
        resp = (
            supabase.table("orders")
            .select("*")
            .in_("status", ["NEW", "PARTIALLY_FILLED"])
            .order("created_at", desc=False)
            .execute()
        )
        orders = resp.data if resp.data else []

        logger.info(f"Found {len(orders)} active orders to hydrate.")
        for o in orders:
            cpp_quantity = int(float(o["quantity"]) * 1_000_000)
            order_type = (
                _nanotrade_ext.OrderType.BUY
                if o["side"] == "BUY"
                else _nanotrade_ext.OrderType.SELL
            )

            # Use original creation timestamp
            ts_obj = datetime.fromisoformat(o["created_at"].replace("Z", "+00:00"))
            ts_ms = int(ts_obj.timestamp() * 1000)

            cpp_order = _nanotrade_ext.Order(
                o["id"],
                order_type,
                float(o["price"]),
                cpp_quantity,
                ts_ms,
                o["user_id"],
                not o["is_bot"],
            )

            # Process in engine silently (no DB updates during hydration)
            # Since these are already NEW or PARTIALLY_FILLED, they shouldn't match against each other
            # if the previous state was consistent. If they do match, it means the DB was inconsistent.
            self.engine.process_order(cpp_order)

        logger.info("Hydration complete.")
        await self.publish_orderbook()

    async def publish_orderbook(self):
        orderbook_data = self.engine.get_order_book()
        try:
            parsed = json.loads(orderbook_data)
            for side in ["bids", "asks"]:
                if side in parsed:
                    for entry in parsed[side]:
                        if "quantity" in entry:
                            entry["quantity"] = entry["quantity"] / 1_000_000

            await self.redis.set("engine:orderbook", json.dumps(parsed))
            await self.redis.publish(
                "orderbook",
                json.dumps(
                    {
                        "type": "orderbook",
                        "data": parsed,
                        "timestamp": int(datetime.now().timestamp() * 1000),
                    }
                ),
            )
        except Exception as e:
            logger.error(f"Failed to publish orderbook: {e}")

    async def run(self):
        await self.init_stream()
        await self.hydrate_engine()

        logger.info("Starting order consumption loop...")
        while True:
            try:
                # Block for up to 1 second
                messages = await self.redis.xreadgroup(
                    GROUP_NAME, CONSUMER_NAME, {STREAM_KEY: ">"}, count=10, block=1000
                )

                if not messages:
                    # Periodically check for pending messages (crash recovery from PEL)
                    pending = await self.redis.xpending(STREAM_KEY, GROUP_NAME)
                    if pending and pending["pending"] > 0:
                        # Claim messages idle for > 10 seconds
                        claimed = await self.redis.xautoclaim(
                            STREAM_KEY,
                            GROUP_NAME,
                            CONSUMER_NAME,
                            min_idle_time=10000,
                            start_id="0-0",
                            count=10,
                        )
                        if claimed and claimed[1]:
                            logger.info(
                                f"Claimed {len(claimed[1])} pending messages from crashed workers"
                            )
                            await self.process_messages(claimed[1])
                    continue

                for _stream, msg_list in messages:
                    await self.process_messages(msg_list)

            except Exception as e:
                logger.error(f"Error in stream loop: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def process_messages(self, messages):
        for msg_id, data in messages:
            order_id = data.get("order_id")

            try:
                # 1. Update state to PROCESSING
                supabase.table("orders").update({"status": "PROCESSING"}).eq(
                    "id", order_id
                ).execute()

                # 2. Process Order
                await self.execute_order(data)

                # 3. Acknowledge message
                await self.redis.xack(STREAM_KEY, GROUP_NAME, msg_id)
                logger.info(f"Successfully processed and ACKed msg_id={msg_id}")

            except Exception as e:
                logger.error(f"Failed to process order {order_id}: {e}", exc_info=True)
                # Implement DLQ logic
                retries = await self.redis.hincrby(f"retries:{msg_id}", "count", 1)
                if retries >= 3:
                    logger.critical(f"Order {order_id} failed 3 times. Moving to DLQ.")
                    supabase.table("orders").update({"status": "FAILED"}).eq(
                        "id", order_id
                    ).execute()
                    await self.redis.xadd(DLQ_STREAM, data)
                    await self.redis.xack(STREAM_KEY, GROUP_NAME, msg_id)
                else:
                    logger.warning(f"Will retry order {order_id} (Attempt {retries}/3)")

    async def execute_order(self, data):
        order_id = data["order_id"]
        user_id = data["user_id"]
        side = data["side"]
        price = float(data["price"])
        quantity = float(data["quantity"])
        is_user = data["is_user"] == "True"
        timestamp_ms = int(data["timestamp"])

        cpp_quantity = int(quantity * 1_000_000)
        order_type = (
            _nanotrade_ext.OrderType.BUY
            if side == "BUY"
            else _nanotrade_ext.OrderType.SELL
        )

        cpp_order = _nanotrade_ext.Order(
            order_id, order_type, price, cpp_quantity, timestamp_ms, user_id, is_user
        )

        # Execute in engine
        result = self.engine.process_order(cpp_order)
        unscaled_rem_qty = result.remaining_quantity / 1_000_000

        # Handle trades
        for t in result.trades:
            unscaled_trade_qty = t.quantity / 1_000_000
            is_bot_trade = (
                t.buyer_id == "00000000-0000-0000-0000-000000000000"
                or t.seller_id == "00000000-0000-0000-0000-000000000000"
            )

            # Atomic settlement via RPC
            # Ensure trade_id is treated as string
            trade_ts = datetime.fromtimestamp(
                t.timestamp / 1000.0, tz=timezone.utc
            ).isoformat()

            rpc_payload = {
                "p_trade_id": t.trade_id,
                "p_buyer_id": t.buyer_id,
                "p_seller_id": t.seller_id,
                "p_price": float(t.price),
                "p_quantity": float(unscaled_trade_qty),
                "p_buy_order_id": t.buy_order_id,
                "p_sell_order_id": t.sell_order_id,
                "p_is_bot_trade": is_bot_trade,
                "p_trade_timestamp": trade_ts,
            }

            supabase.rpc("settle_trade_atomic", rpc_payload).execute()

            # Update matched maker order quantity manually since RPC doesn't do it
            matched_order_id = t.sell_order_id if side == "BUY" else t.buy_order_id
            maker_db = (
                supabase.table("orders")
                .select("quantity")
                .eq("id", matched_order_id)
                .execute()
            )
            if maker_db.data:
                maker_qty = float(maker_db.data[0]["quantity"])
                new_maker_qty = max(0.0, maker_qty - unscaled_trade_qty)
                maker_status = "FILLED" if new_maker_qty < 1e-6 else "PARTIALLY_FILLED"
                supabase.table("orders").update(
                    {"quantity": new_maker_qty, "status": maker_status}
                ).eq("id", matched_order_id).execute()

            # Publish trade to Redis
            trade_dict = {
                "trade_id": t.trade_id,
                "buy_order_id": t.buy_order_id,
                "sell_order_id": t.sell_order_id,
                "price": t.price,
                "quantity": unscaled_trade_qty,
                "timestamp": t.timestamp,
                "buyer_id": t.buyer_id,
                "seller_id": t.seller_id,
            }
            await self.redis.publish(
                "trade",
                json.dumps(
                    {"type": "trade", "data": trade_dict, "timestamp": timestamp_ms}
                ),
            )

        # Update taker order status
        supabase.table("orders").update(
            {"quantity": unscaled_rem_qty, "status": result.fill_status}
        ).eq("id", order_id).execute()

        await self.publish_orderbook()


if __name__ == "__main__":
    daemon = EngineDaemon()
    asyncio.run(daemon.run())
