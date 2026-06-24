import asyncio
import json
import time
import redis.asyncio as redis
import websockets

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# Note: We must use async redis so we don't block the asyncio event loop
r = redis.from_url(settings.REDIS_URL, decode_responses=True)

BINANCE_STREAM_URL = (
    "wss://stream.binance.com:9443/stream?"
    "streams=btcusdt@ticker/"
    "btcusdt@trade/"
    "btcusdt@kline_1m"
)

async def handle_price(data):
    usd_price = float(data["c"])

    rate_str = await r.get(settings.REDIS_KEY_USD_INR_RATE)
    rate = float(rate_str) if rate_str else 83.5

    inr_price = round(usd_price * rate, 2)

    # Store latest price
    await r.set("price:btc_inr", inr_price)

    # Publish event
    event = {
        "type": "price",
        "data": {
            "usd": usd_price,
            "inr": inr_price,
            "rate": rate,
        },
        "ts": int(time.time() * 1000),
    }

    await r.publish("market:price", json.dumps(event))

async def handle_trade(data):
    trade = {
        "price": float(data["p"]),
        "quantity": float(data["q"]),
        "side": "BUY" if data["m"] is False else "SELL",
        "ts": data["T"],
    }

    # Store last 100 trades
    await r.lpush("trades:btc", json.dumps(trade))
    await r.ltrim("trades:btc", 0, 100)

    event = {
        "type": "market_trade",
        "data": trade
    }
    await r.publish("market:trades", json.dumps(event))

async def handle_kline(data):
    k = data["k"]

    candle = {
        "open": float(k["o"]),
        "high": float(k["h"]),
        "low": float(k["l"]),
        "close": float(k["c"]),
        "volume": float(k["v"]),
        "start": k["t"],
        "end": k["T"],
    }

    await r.set("kline:btc:1m", json.dumps(candle))
    event = {
        "type": "kline",
        "data": candle
    }
    await r.publish("market:kline", json.dumps(event))

async def market_data_listener():
    url = BINANCE_STREAM_URL
    logger.info(f"[Market] Connecting to Binance stream: {url}")

    while True:
        try:
            async with websockets.connect(url) as ws:
                logger.info("[Market] Connected to Binance WebSocket")

                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)

                    stream = data.get("stream")
                    payload = data.get("data")

                    if not stream or not payload:
                        continue

                    if "ticker" in stream:
                        await handle_price(payload)

                    elif "trade" in stream:
                        await handle_trade(payload)

                    elif "kline" in stream:
                        await handle_kline(payload)
                        
        except Exception as e:
            logger.error(f"[Market] WebSocket disconnected: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)
