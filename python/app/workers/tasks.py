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
def run_fx_converter():
    """
    Long-running periodic daemon task that fetches the USD-INR FX rate
    from a public API (or fallback) every 10 seconds and caches it in Redis.
    """
    print("Starting FX converter daemon...")
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    while True:
        try:
            # Fetch latest exchange rates with USD base
            resp = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                rate = data.get("rates", {}).get("INR")
                if rate:
                    r.set(settings.REDIS_KEY_USD_INR_RATE, str(rate))
                    print(f"FX converter: Updated cached USD_INR_RATE to {rate}")
                else:
                    print("FX converter: INR rate not found in API response")
            else:
                print(f"FX converter: API request failed with status {resp.status_code}")
        except Exception as e:
            print(f"FX converter: Error fetching exchange rate: {e}")
            
        # Update rate every 10 seconds (NOT per tick)
        time.sleep(10)

@celery_app.task
def run_binance_feed():
    """
    Long-running daemon task subscribing to public Binance WebSocket feed
    for BTC/USDT trades, converting USD to INR using the cached FX rate,
    and storing the reference price in Redis.
    """
    print("Starting Binance reference price feed listener...")
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    async def listen():
        url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
        async with websockets.connect(url) as ws:
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                usd_price_str = data.get("p")  # 'p' is the trade price
                if usd_price_str:
                    usd_price = float(usd_price_str)
                    
                    # Read current USD-INR rate from Redis
                    rate_str = r.get(settings.REDIS_KEY_USD_INR_RATE)
                    rate = float(rate_str) if rate_str else 83.5
                    
                    # Convert to INR reference price (Price precision is 2 decimals)
                    reference_price_inr = round(usd_price * rate, 2)
                    
                    # Store reference price in Redis
                    r.set(settings.REDIS_KEY_REFERENCE_PRICE, str(reference_price_inr))
                    
                    # Publish price update event to Redis
                    price_event = {
                        "type": "price",
                        "data": {
                            "binance_price_usd": usd_price,
                            "usd_inr_rate": rate,
                            "reference_price_inr": reference_price_inr
                        },
                        "timestamp": int(time.time() * 1000)
                    }
                    r.publish("price", json.dumps(price_event))
                    
    try:
        asyncio.run(listen())
    except Exception as e:
        print(f"Binance feed encountered error: {e}")
        # Let the task finish so Celery can restart it if needed

@celery_app.task
def run_market_simulator():
    """
    Synthetic market simulator generating noise, momentum, clustering, and whale orders
    around the Binance reference price. Submits orders to C++ engine via FastAPI.
    """
    print("Starting market simulator...")
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    api_url = f"http://{settings.HOST}:{settings.PORT}/orders/simulator"
    
    while True:
        # 1. Fetch current Binance reference price (INR) from Redis
        price_str = r.get(settings.REDIS_KEY_REFERENCE_PRICE)
        if not price_str:
            price = 5594500.0  # Fallback price (~67k USD * 83.5)
        else:
            price = float(price_str)
            
        # 2. Determine side and spread
        # spread ranges between 0.02% and 0.5% (0.0002 to 0.005)
        spread = random.uniform(0.0002, 0.005)
        
        # 3. Determine if this is a "whale" order (5% probability)
        is_whale = random.random() < 0.05
        if is_whale:
            # Whale trades larger volumes (1.5 to 5.0 BTC)
            quantity = round(random.uniform(1.5, 5.0), 6)
            # Whales can cause larger price shifts (up to 1.5% spread)
            spread = random.uniform(0.005, 0.015)
        else:
            # Normal user trades smaller volumes (0.001 to 0.05 BTC)
            quantity = round(random.uniform(0.001, 0.05), 6)

        # 4. Decide on clustering (place multiple orders close to each other)
        # 30% probability of clustering
        is_cluster = random.random() < 0.3
        
        sides = ["BUY", "SELL"]
        side = random.choice(sides)
        
        # We can place one order or a cluster of orders
        orders_to_place = []
        if is_cluster:
            cluster_size = random.randint(2, 4)
            base_qty = quantity / cluster_size
            for i in range(cluster_size):
                # Spread increases slightly for each outer shell of the cluster
                layer_spread = spread + (i * 0.0005)
                if side == "BUY":
                    order_price = round(price * (1 - layer_spread), 2)
                else:
                    order_price = round(price * (1 + layer_spread), 2)
                
                # Small quantity variation within cluster
                qty_var = base_qty * random.uniform(0.8, 1.2)
                orders_to_place.append((side, order_price, round(qty_var, 6)))
        else:
            if side == "BUY":
                order_price = round(price * (1 - spread), 2)
            else:
                order_price = round(price * (1 + spread), 2)
            orders_to_place.append((side, order_price, quantity))

        # 5. Submit to C++ engine via local API
        for s, p, q in orders_to_place:
            try:
                payload = {
                    "side": s,
                    "price": p,
                    "quantity": q
                }
                resp = requests.post(api_url, json=payload, timeout=2)
                if resp.status_code == 200:
                    msg = "Whale" if is_whale else "Simulator"
                    print(f"{msg} placed {s} order: {q:.6f} BTC @ ₹{p:.2f}")
                else:
                    print(f"Simulator placement rejected: {resp.status_code} - {resp.text}")
            except Exception as e:
                print(f"Simulator failed to connect to FastAPI engine: {e}")
                
        # Random sleep interval between simulator actions (0.2s to 1.5s)
        time.sleep(random.uniform(0.2, 1.5))
