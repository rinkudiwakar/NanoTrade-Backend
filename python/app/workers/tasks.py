import asyncio
import json
import random
import time
import requests
import redis
import websockets
from app.workers.celery_app import celery_app
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


@celery_app.task
def run_fx_converter():
    """
    Long-running periodic daemon task that fetches the USD-INR FX rate
    from a public API (or fallback) every 10 seconds and caches it in Redis.
    """
    logger.info("[FX] FX converter task started")
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    consecutive_failures = 0

    while True:
        try:
            logger.debug("[FX] Fetching USD-INR rate from open.er-api.com")
            resp = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                rate = data.get("rates", {}).get("INR")
                if rate:
                    r.set(settings.REDIS_KEY_USD_INR_RATE, str(rate))
                    consecutive_failures = 0
                    logger.info(f"[FX] USD_INR_RATE updated | rate={rate}")
                else:
                    logger.warning("[FX] INR rate key missing in API response")
            else:
                consecutive_failures += 1
                logger.warning(
                    f"[FX] API request failed | status={resp.status_code} failures={consecutive_failures}"
                )
        except Exception as e:
            consecutive_failures += 1
            logger.error(
                f"[FX] Error fetching exchange rate | error={e} failures={consecutive_failures}",
                exc_info=True,
            )

        logger.debug("[FX] Sleeping 10s before next FX update")
        time.sleep(10)


@celery_app.task
def run_binance_feed():
    """
    Long-running daemon task subscribing to public Binance WebSocket feed
    for BTC/USDT trades, converting USD to INR using the cached FX rate,
    and storing the reference price in Redis.
    """
    logger.info("[Binance] Binance feed task started")
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    tick_count = 0

    async def listen():
        nonlocal tick_count
        url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
        logger.info(f"[Binance] Connecting to WebSocket | url={url}")
        async with websockets.connect(url) as ws:
            logger.info("[Binance] WebSocket connected")
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                usd_price_str = data.get("p")  # 'p' is the trade price
                if usd_price_str:
                    usd_price = float(usd_price_str)

                    # Read current USD-INR rate from Redis
                    rate_str = r.get(settings.REDIS_KEY_USD_INR_RATE)
                    rate = float(rate_str) if rate_str else 83.5

                    # Convert to INR reference price (2 decimal precision)
                    reference_price_inr = round(usd_price * rate, 2)

                    # Store reference price in Redis
                    r.set(settings.REDIS_KEY_REFERENCE_PRICE, str(reference_price_inr))

                    tick_count += 1
                    # Log every 50 ticks to avoid flooding (Binance sends ~2 ticks/sec)
                    if tick_count % 50 == 1:
                        logger.info(
                            f"[Binance] Price tick | usd={usd_price} rate={rate} inr={reference_price_inr} ticks={tick_count}"
                        )
                    else:
                        logger.debug(
                            f"[Binance] Tick | usd={usd_price} inr={reference_price_inr}"
                        )

                    # Publish price update event to Redis
                    price_event = {
                        "type": "price",
                        "data": {
                            "binance_price_usd": usd_price,
                            "usd_inr_rate": rate,
                            "reference_price_inr": reference_price_inr,
                        },
                        "timestamp": int(time.time() * 1000),
                    }
                    r.publish("price", json.dumps(price_event))

    try:
        logger.info("[Binance] Starting asyncio event loop for WebSocket feed")
        asyncio.run(listen())
    except Exception as e:
        logger.error(f"[Binance] Feed terminated with error | error={e}", exc_info=True)


@celery_app.task
def run_market_simulator():
    """
    Synthetic market simulator that generates realistic orders around the
    Binance reference price and submits them to the C++ engine via FastAPI.

    Order generation logic lives in app/services/simulator_service.py.
    This task handles only the Celery/Redis/HTTP orchestration layer.

    Requires SIMULATOR_SECRET to be set in .env to protect the
    /orders/simulator endpoint from external callers.
    """
    from app.services.simulator_service import generate_simulator_orders

    logger.info("[Simulator] Market simulator task started")
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    api_url = f"http://{settings.HOST}:{settings.PORT}/orders/simulator"
    simulator_secret = settings.SIMULATOR_SECRET
    tick_count = 0

    if not simulator_secret:
        logger.error(
            "[Simulator] SIMULATOR_SECRET not set in .env — simulator will not run"
        )
        return

    logger.info(f"[Simulator] Targeting FastAPI at {api_url}")

    while True:
        # 1. Fetch current Binance reference price (INR) from Redis
        price_str = r.get(settings.REDIS_KEY_REFERENCE_PRICE)
        if not price_str:
            reference_price = 5594500.0  # Fallback: ~67,000 USD * 83.5 INR/USD
            logger.warning(
                f"[Simulator] No reference price in Redis — using fallback ₹{reference_price:,.2f}"
            )
        else:
            reference_price = float(price_str)

        # 2. Generate orders via simulator service (all trader types handled inside)
        try:
            orders_to_place = generate_simulator_orders(reference_price)
            logger.debug(
                f"[Simulator] Generated {len(orders_to_place)} order(s) | ref_price=₹{reference_price:,.2f}"
            )
        except Exception as e:
            logger.error(
                f"[Simulator] Order generation error | error={e}", exc_info=True
            )
            time.sleep(1.0)
            continue

        # 3. Submit each order to the C++ engine via the internal FastAPI endpoint
        for order in orders_to_place:
            try:
                payload = {
                    "side": order.side,
                    "price": order.price,
                    "quantity": order.quantity,
                }
                resp = requests.post(
                    api_url,
                    json=payload,
                    headers={"X-Simulator-Secret": simulator_secret},
                    timeout=2,
                )
                if resp.status_code == 200:
                    tick_count += 1
                    # Log every 20 orders to avoid flood
                    if tick_count % 20 == 1:
                        logger.info(
                            f"[Simulator] Order submitted | {order.side} {order.quantity:.6f} BTC @ ₹{order.price:.2f} tick={tick_count}"
                        )
                    else:
                        logger.debug(
                            f"[Simulator] {order.side} {order.quantity:.6f} BTC @ ₹{order.price:.2f}"
                        )
                else:
                    logger.warning(
                        f"[Simulator] Order rejected | status={resp.status_code} body={resp.text[:120]}"
                    )
            except requests.exceptions.ConnectionError:
                logger.error(
                    "[Simulator] Cannot connect to FastAPI — is the server running?"
                )
            except Exception as e:
                logger.error(
                    f"[Simulator] Unexpected error submitting order | error={e}",
                    exc_info=True,
                )

        # 4. Random sleep between ticks (0.2s – 1.5s mimics realistic order flow)
        sleep_time = random.uniform(0.2, 1.5)
        logger.debug(f"[Simulator] Sleeping {sleep_time:.2f}s before next tick")
        time.sleep(sleep_time)
