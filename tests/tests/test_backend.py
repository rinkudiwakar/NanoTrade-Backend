"""
test_backend.py — Unit tests for NanoTrade backend services.

These tests are fully isolated (no live Supabase, Redis, or C++ engine required).
All external dependencies are mocked via conftest.py or within each test.

Run:
    cd python && pytest ../tests/test_backend.py -v
"""

import json
from unittest.mock import MagicMock, AsyncMock, patch, call

import pytest


# ─────────────────────────────────────────────────────────────
# Portfolio Service — validate_user_funds
# ─────────────────────────────────────────────────────────────

class TestValidateUserFunds:
    """Tests for app.services.portfolio_service.validate_user_funds"""

    @pytest.mark.asyncio
    @patch("app.services.portfolio_service.supabase")
    async def test_buy_insufficient_balance_raises(self, mock_db):
        from app.services.portfolio_service import validate_user_funds

        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"balance": 1000.00}]
        )

        # Requires ₹1200 (100 × 12) — should raise
        with pytest.raises(ValueError, match="Insufficient balance"):
            await validate_user_funds(
                user_id="847a5202-3fae-4cde-a597-1097a4a1a6ab",
                side="BUY",
                price=100.0,
                quantity=12.0,
            )

    @pytest.mark.asyncio
    @patch("app.services.portfolio_service.supabase")
    async def test_buy_sufficient_balance_passes(self, mock_db):
        from app.services.portfolio_service import validate_user_funds

        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"balance": 5000.00}]
        )

        # Requires ₹4500 (900 × 5) — should not raise
        await validate_user_funds(
            user_id="847a5202-3fae-4cde-a597-1097a4a1a6ab",
            side="BUY",
            price=900.0,
            quantity=5.0,
        )

    @pytest.mark.asyncio
    @patch("app.services.portfolio_service.supabase")
    async def test_sell_insufficient_holdings_raises(self, mock_db):
        from app.services.portfolio_service import validate_user_funds

        # Chain: .table().select().eq().eq().execute()
        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"quantity": 0.005}]
        )

        # Wants to sell 0.01 BTC but only has 0.005 BTC — should raise
        with pytest.raises(ValueError, match="Insufficient BTC holdings"):
            await validate_user_funds(
                user_id="847a5202-3fae-4cde-a597-1097a4a1a6ab",
                side="SELL",
                price=5_500_000.0,
                quantity=0.01,
            )

    @pytest.mark.asyncio
    @patch("app.services.portfolio_service.supabase")
    async def test_sell_sufficient_holdings_passes(self, mock_db):
        from app.services.portfolio_service import validate_user_funds

        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"quantity": 0.05}]
        )

        # Wants to sell 0.02 BTC, has 0.05 BTC — should not raise
        await validate_user_funds(
            user_id="847a5202-3fae-4cde-a597-1097a4a1a6ab",
            side="SELL",
            price=5_500_000.0,
            quantity=0.02,
        )

    @pytest.mark.asyncio
    async def test_bot_user_bypasses_validation(self):
        """System bot (nil UUID) must never hit the DB."""
        from app.services.portfolio_service import validate_user_funds

        # Should return without any DB interaction
        await validate_user_funds(
            user_id="00000000-0000-0000-0000-000000000000",
            side="BUY",
            price=5_000_000.0,
            quantity=10.0,
        )

    @pytest.mark.asyncio
    @patch("app.services.portfolio_service.supabase")
    async def test_invalid_uuid_bypasses_validation(self, mock_db):
        """Non-UUID user IDs (invalid strings) should bypass fund validation."""
        from app.services.portfolio_service import validate_user_funds

        await validate_user_funds(
            user_id="not-a-real-uuid",
            side="BUY",
            price=100.0,
            quantity=999.0,
        )
        mock_db.table.assert_not_called()


# ─────────────────────────────────────────────────────────────
# Portfolio Service — is_valid_uuid
# ─────────────────────────────────────────────────────────────

class TestIsValidUUID:
    def test_valid_uuid_returns_true(self):
        from app.services.portfolio_service import is_valid_uuid
        assert is_valid_uuid("847a5202-3fae-4cde-a597-1097a4a1a6ab") is True

    def test_nil_uuid_returns_true(self):
        from app.services.portfolio_service import is_valid_uuid
        assert is_valid_uuid("00000000-0000-0000-0000-000000000000") is True

    def test_invalid_string_returns_false(self):
        from app.services.portfolio_service import is_valid_uuid
        assert is_valid_uuid("not-a-uuid") is False

    def test_empty_string_returns_false(self):
        from app.services.portfolio_service import is_valid_uuid
        assert is_valid_uuid("") is False


# ─────────────────────────────────────────────────────────────
# Order Service — place_order (Redis Stream Enqueue)
# ─────────────────────────────────────────────────────────────

class TestPlaceOrder:

    @pytest.mark.asyncio
    @patch("app.services.order_service.supabase")
    @patch("app.services.order_service.validate_user_funds", new_callable=AsyncMock)
    async def test_order_enqueued_to_redis(
        self, mock_validate, mock_db
    ):
        from app.services.order_service import place_order

        # Mock DB insert
        insert_exec = MagicMock(data=[{"id": "00000000-0000-0000-0000-111111111111"}])
        mock_db.table.return_value.insert.return_value.execute.return_value = insert_exec

        redis = AsyncMock()
        redis.get.return_value = None  # Needed for RedisLock.owned()

        result = await place_order(
            user_id="00000000-0000-0000-0000-111111111111",
            is_user=True,
            side="BUY",
            price=5_500_000.0,
            quantity=0.005,
            redis_client=redis,
        )

        assert result["status"] == "QUEUED"
        assert result["message"] == "Order queued for matching."
        
        # Verify redis xadd was called
        redis.xadd.assert_called_once()
        args = redis.xadd.call_args[0]
        assert args[0] == "engine:orders_stream"
        
        payload = args[1]
        assert "order_id" in payload
        assert float(payload["price"]) == 5_500_000.0
        assert float(payload["quantity"]) == 0.005
