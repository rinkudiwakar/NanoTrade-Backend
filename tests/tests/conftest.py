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
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def mock_supabase_session(request):
    """
    Replace the `supabase` client singleton with a MagicMock for unit tests.
    Skip mocking for load tests (marked with @pytest.mark.load) and the live user test.
    """

    # 🔥 Skip mocking for load tests and integration tests
    if "test_live_user" in request.node.nodeid or request.node.get_closest_marker("load"):
        yield
        return

    with patch("app.core.database.supabase", new_callable=MagicMock) as _mock:
        # Also patch service layer references
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
