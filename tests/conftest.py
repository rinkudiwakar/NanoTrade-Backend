"""
conftest.py — shared pytest fixtures and session-level mocks.

Key responsibilities:
  1. Patch `supabase` singleton BEFORE any app module is imported so that
     unit tests never try to reach a live Supabase instance.
  2. Provide a reusable mock C++ engine fixture.
  3. Ensure the `python/` directory and `build/` directory are on sys.path
     so that `app.*` and `_nanotrade_ext` can be imported.
"""

import sys
import os
import json
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

# ── Path setup ──────────────────────────────────────────────────────────────
# Make `app` importable from tests/ directory
PYTHON_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python"))
BUILD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "build"))

if PYTHON_DIR not in sys.path:
    sys.path.insert(0, PYTHON_DIR)
if BUILD_DIR not in sys.path:
    sys.path.insert(0, BUILD_DIR)


# ── Session-level supabase mock ──────────────────────────────────────────────
# Patch before any app import to avoid a live network call during module load.
@pytest.fixture(autouse=True, scope="session")
def mock_supabase_session():
    """
    Replace the `supabase` client singleton with a MagicMock for the entire
    test session. Individual tests can further refine this mock.
    """
    with patch("app.core.database.supabase", new_callable=MagicMock) as _mock:
        # Also patch the already-imported references in service modules
        with patch("app.services.order_service.supabase", _mock):
            with patch("app.services.portfolio_service.supabase", _mock):
                yield _mock


# ── Reusable engine mock fixture ─────────────────────────────────────────────
@pytest.fixture
def mock_engine():
    """Return a MagicMock that behaves like `_nanotrade_ext.MatchingEngine`."""
    engine = MagicMock()
    engine.get_order_book.return_value = json.dumps({"bids": [], "asks": []})
    engine.get_last_traded_price.return_value = 0.0

    result = MagicMock()
    result.trades = []
    result.remaining_quantity = 0
    result.fill_status = "NEW"
    engine.process_order.return_value = result

    return engine


@pytest.fixture
def mock_redis():
    """Return an AsyncMock that behaves like an aioredis client."""
    r = AsyncMock()
    r.get.return_value = None
    r.set.return_value = True
    r.publish.return_value = 1
    return r
