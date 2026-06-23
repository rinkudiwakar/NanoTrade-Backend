import time
import uuid
from datetime import datetime, timezone
from redis.asyncio.lock import Lock as RedisLock

from app.core.database import supabase
from app.core.logger import get_logger
from app.services.portfolio_service import validate_user_funds

logger = get_logger(__name__)


async def place_order(
    user_id: str, is_user: bool, side: str, price: float, quantity: float, redis_client
) -> dict:
    """
    Validates user funds and places a limit order into the matching queue.
    Uses granular distributed locks (INR for BUY, BTC for SELL) to prevent
    concurrent validation races. Does NOT execute the engine synchronously.
    """
    order_id = str(uuid.uuid4())
    logger.info(
        f"place_order start | user_id={user_id} side={side} price={price} qty={quantity} order_id={order_id} is_user={is_user}"
    )

    timestamp_ms = int(time.time() * 1000)
    created_at_iso = datetime.now(timezone.utc).isoformat()
    is_bot = not is_user or user_id == "00000000-0000-0000-0000-000000000000"
    source = "simulator" if is_bot else "user"

    # 1. Granular Lock for real users
    lock = None
    if not is_bot:
        asset_to_lock = "INR" if side == "BUY" else "BTC"
        lock_key = f"lock:user:{user_id}:{asset_to_lock}"
        lock = RedisLock(redis_client, lock_key, timeout=5.0, blocking_timeout=2.0)
        logger.debug(f"Acquiring lock | key={lock_key}")
        acquired = await lock.acquire()
        if not acquired:
            logger.error(f"Failed to acquire lock | key={lock_key}")
            raise Exception(
                "Order placement timed out while acquiring lock. Please try again."
            )

    try:
        # 2. Pre-execution validation
        if not is_bot:
            logger.debug(f"Validating funds | user_id={user_id} side={side}")
            await validate_user_funds(user_id, side, price, quantity)
            logger.debug(f"Fund validation passed | user_id={user_id}")

        # 3. Insert order into database as QUEUED
        logger.debug(f"Inserting order into DB | order_id={order_id} source={source}")
        order_db_resp = (
            supabase.table("orders")
            .insert(
                {
                    "id": order_id,
                    "user_id": user_id,
                    "side": side,
                    "price": price,
                    "quantity": quantity,
                    "status": "QUEUED",
                    "is_bot": is_bot,
                    "source": source,
                    "created_at": created_at_iso,
                }
            )
            .execute()
        )

        if not order_db_resp.data:
            logger.error(f"DB insert failed | order_id={order_id}")
            raise Exception("Failed to insert order into database")
        logger.debug(f"Order inserted in DB OK | order_id={order_id}")

        # 4. Push order to Redis Stream for the worker daemon
        stream_payload = {
            "order_id": order_id,
            "user_id": user_id,
            "is_user": str(is_user),
            "side": side,
            "price": str(price),
            "quantity": str(quantity),
            "timestamp": str(timestamp_ms),
        }

        # XADD command adds to the stream
        await redis_client.xadd("engine:orders_stream", stream_payload)
        logger.info(
            f"Order added to Redis Stream 'engine:orders_stream' | order_id={order_id}"
        )

    finally:
        if lock and await lock.owned():
            await lock.release()
            logger.debug(f"Lock released | user_id={user_id}")

    return {
        "order_id": order_id,
        "status": "QUEUED",
        "message": "Order queued for matching.",
    }
