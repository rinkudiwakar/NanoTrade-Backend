"""
load_testing.py — Concurrent load test for the NanoTrade order placement endpoint.

Marked as `pytest.mark.load` so it is NEVER collected in CI or normal test runs.
Run manually against a running server:

    # Set token in your shell first:
    set NANOTRADE_TEST_JWT=<your-supabase-jwt>        (Windows)
    export NANOTRADE_TEST_JWT=<your-supabase-jwt>      (Linux/Mac)

    cd python && pytest ../tests/load_testing.py -v -m load
"""

import os
import threading

import pytest
import requests

# ── Configuration ─────────────────────────────────────────────────────────────
URL = "http://localhost:8000/orders"
CONCURRENCY = 50

# Read the JWT from the environment — never hardcode tokens in source files.
TOKEN = os.environ.get("NANOTRADE_TEST_JWT", "")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

ORDER_PAYLOAD = {
    "side": "BUY",
    "price": 5_000_000,
    "quantity": 0.001,
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _place_one_order(results: list, idx: int) -> None:
    """Send a single order and store (status_code, response_text) in results."""
    try:
        resp = requests.post(URL, headers=HEADERS, json=ORDER_PAYLOAD, timeout=10)
        results[idx] = (resp.status_code, resp.text)
    except Exception as exc:
        results[idx] = (0, str(exc))


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.load
def test_jwt_token_configured():
    """Fail fast if the test JWT is missing — prevents meaningless 401 flood."""
    assert TOKEN, (
        "NANOTRADE_TEST_JWT environment variable is not set. "
        "Export it before running load tests."
    )


@pytest.mark.load
def test_concurrent_order_placement():
    """
    Fire CONCURRENCY simultaneous BUY orders and assert:
      - All requests completed (no crashes / timeouts)
      - >= 80% returned HTTP 200 (acceptable under contention)
    """
    if not TOKEN:
        pytest.skip("NANOTRADE_TEST_JWT not set — skipping load test")

    results: list = [None] * CONCURRENCY
    threads = [
        threading.Thread(target=_place_one_order, args=(results, i))
        for i in range(CONCURRENCY)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    completed = [r for r in results if r is not None]
    successful = [r for r in completed if r[0] == 200]

    assert len(completed) == CONCURRENCY, "Not all threads completed"
    success_rate = len(successful) / CONCURRENCY
    assert success_rate >= 0.8, (
        f"Success rate {success_rate:.0%} below 80% threshold. "
        f"Failures: {[r for r in completed if r[0] != 200]}"
    )