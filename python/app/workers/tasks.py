import asyncio
import json
import random
import time

import redis
import requests
import websockets

from app.core.config import settings
from app.core.logger import get_logger
from app.workers.celery_app import celery_app

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
    api_url = f"{settings.API_URL}/orders/simulator"
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
        price_str = r.get("price:btc_inr")
        if not price_str:
            reference_price = 5594500.0  # Default Fallback
            try:
                # Try fetching from REST API as fallback if WebSocket failed or isn't running
                resp = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3)
                if resp.status_code == 200:
                    data = resp.json()
                    usd_price = float(data["price"])
                    rate_str = r.get(settings.REDIS_KEY_USD_INR_RATE)
                    rate = float(rate_str) if rate_str else 83.5
                    reference_price = round(usd_price * rate, 2)
                    logger.info(f"[Simulator] Using REST API fallback reference price: ₹{reference_price:,.2f}")
                    # Briefly cache it to avoid spamming REST API on every tick
                    r.set("price:btc_inr", str(reference_price), ex=10)
            except Exception as e:
                logger.warning(
                    f"[Simulator] No reference price in Redis and REST failed ({e}) — using hard fallback ₹{reference_price:,.2f}"
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
