import requests
import threading

URL = "http://localhost:8000/orders"
TOKEN = "YOUR_SUPABASE_JWT"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def place_order():
    requests.post(
        URL,
        headers=headers,
        json={
            "side": "BUY",
            "price": 5000000,
            "quantity": 0.001
        }
    )

threads = []
for _ in range(50):
    t = threading.Thread(target=place_order)
    t.start()
    threads.append(t)

for t in threads:
    t.join()