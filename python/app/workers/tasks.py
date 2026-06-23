import asyncio
import json
import random
import time
import requests
import redis
import websockets
from app.workers.celery_app import celery_app
from app.core.config import settings

@celery_app.task
def run_binance_feed():
    """
    Long-running daemon task subscribing to public Binance WebSocket feed
    for BTC/USDT trades, storing the reference price in Redis.
    """
    print("Starting Binance reference price feed listener...")
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    async def listen():
        url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
        async with websockets.connect(url) as ws:
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                price = data.get("p")  # 'p' is the trade price
                if price:
                    # Store as reference price in Redis
                    r.set("binance_price", price)
                    # Publish reference price updates to Redis
                    r.publish("binance_price_ref", price)
                    
    try:
        asyncio.run(listen())
    except Exception as e:
        print(f"Binance feed encountered error: {e}")
        # Retry logic could go here
        
@celery_app.task
def run_market_simulator():
    """
    Synthetic market simulator generating noise, momentum, and whale orders
    around the Binance reference price. Submits orders to C++ engine via FastAPI.
    """
    print("Starting market simulator...")
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    api_url = f"http://{settings.HOST}:{settings.PORT}/orders/simulator"
    
    while True:
        # 1. Fetch current Binance reference price from Redis
        price_str = r.get("binance_price")
        if not price_str:
            price = 65000.0  # Fallback price
        else:
            price = float(price_str)
            
        # 2. Generate synthetic orders
        side = random.choice(["BUY", "SELL"])
        spread = random.uniform(0.0001, 0.003)  # 0.01% to 0.3% spread
        
        if side == "BUY":
            # Buy order slightly below reference price to build bid depth
            order_price = round(price * (1 - spread), 2)
        else:
            # Sell order slightly above reference price to build ask depth
            order_price = round(price * (1 + spread), 2)
            
        quantity = random.randint(1, 5)
        
        # 3. Submit to C++ engine via local API
        try:
            payload = {
                "side": side,
                "price": order_price,
                "quantity": quantity
            }
            resp = requests.post(api_url, json=payload, timeout=2)
            if resp.status_code == 200:
                print(f"Simulator placed {side} order: {quantity} @ {order_price}")
            else:
                print(f"Simulator placement rejected: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"Simulator failed to connect to FastAPI engine: {e}")
            
        # Random sleep interval between simulator actions (0.5s to 2.5s)
        time.sleep(random.uniform(0.5, 2.5))
