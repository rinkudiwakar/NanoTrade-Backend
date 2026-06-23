"""
production_load_test.py — Advanced load testing for NanoTrade

Run:
export NANOTRADE_TEST_JWT="your token"
pytest tests/load_testing.py -v -m load
"""

import os
import threading
import time
import random
import statistics

import pytest
import requests
import dotenv

dotenv.load_dotenv()

# ── CONFIG ─────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"
ORDER_URL = f"{BASE_URL}/orders"

CONCURRENCY = 50
TOTAL_REQUESTS = 200

TOKEN = os.environ.get("NANOTRADE_TEST_JWT", "")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

# ── METRICS ────────────────────────────────────────────────────
latencies = []
status_codes = []
errors = []
lock = threading.Lock()


# ── ORDER GENERATOR ─────────────────────────────────────────────
def generate_order():
    return {
        "side": "BUY" if random.random() < 0.5 else "SELL",
        "price": 5_000_000 + random.randint(-10_000, 10_000),
        "quantity": round(random.uniform(0.001, 0.01), 6),
    }


# ── WORKER ─────────────────────────────────────────────────────
def place_order():
    payload = generate_order()

    start = time.time()

    try:
        resp = requests.post(
            ORDER_URL,
            headers=HEADERS,
            json=payload,
            timeout=5,
        )
        latency = time.time() - start

        with lock:
            latencies.append(latency)
            status_codes.append(resp.status_code)

            if resp.status_code != 200:
                errors.append((resp.status_code, resp.text))

    except Exception as e:
        with lock:
            errors.append((0, str(e)))


# ── TESTS ──────────────────────────────────────────────────────

@pytest.mark.load
def test_token_available():
    assert TOKEN, "Set NANOTRADE_TEST_JWT before running load test"


@pytest.mark.load
def test_production_load():
    if not TOKEN:
        pytest.skip("JWT not provided")

    print("\n🚀 Starting Production Load Test...")

    threads = []
    start_time = time.time()

    for _ in range(TOTAL_REQUESTS):
        t = threading.Thread(target=place_order)
        t.start()
        threads.append(t)

        # Control concurrency window
        if len(threads) >= CONCURRENCY:
            for t in threads:
                t.join()
            threads = []

    # join remaining
    for t in threads:
        t.join()

    end_time = time.time()

    # ── METRICS CALCULATION ─────────────────────────────────────
    total_time = end_time - start_time
    total_requests = len(status_codes)
    success = sum(1 for s in status_codes if s == 200)

    success_rate = success / total_requests if total_requests else 0
    tps = total_requests / total_time if total_time else 0

    avg_latency = statistics.mean(latencies) if latencies else 0
    p95_latency = statistics.quantiles(latencies, n=100)[94] if len(latencies) >= 100 else avg_latency

    # ── OUTPUT ──────────────────────────────────────────────────
    print("\n📊 RESULTS:")
    print(f"Total Requests: {total_requests}")
    print(f"Success Rate: {success_rate:.2%}")
    print(f"Throughput (TPS): {tps:.2f}")
    print(f"Avg Latency: {avg_latency:.3f}s")
    print(f"P95 Latency: {p95_latency:.3f}s")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\n❌ Sample Errors:")
        for e in errors[:5]:
            print(e)

    # ── ASSERTIONS (PROD LEVEL) ─────────────────────────────────
    assert total_requests > 0, "No requests executed"
    assert success_rate >= 0.95, f"Low success rate: {success_rate:.2%}"
    assert avg_latency < 1.0, f"High latency: {avg_latency:.2f}s"