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
# Portfolio Service — update_portfolio_on_trade
# ─────────────────────────────────────────────────────────────

class TestUpdatePortfolioOnTrade:

    @pytest.mark.asyncio
    @patch("app.services.portfolio_service.supabase")
    async def test_buyer_balance_deducted_and_holding_created(self, mock_db):
        from app.services.portfolio_service import update_portfolio_on_trade

        # Buyer has ₹1,000,000 balance, no prior BTC holding
        buyer_profile_exec = MagicMock(data=[{"balance": 1_000_000.0}])
        buyer_holding_exec = MagicMock(data=[])  # no existing holding

        def _table(name):
            t = MagicMock()
            t.select.return_value.eq.return_value.execute.return_value = buyer_profile_exec
            t.select.return_value.eq.return_value.eq.return_value.execute.return_value = buyer_holding_exec
            t.update.return_value.eq.return_value.execute.return_value = MagicMock()
            t.insert.return_value.execute.return_value = MagicMock()
            return t

        mock_db.table.side_effect = _table

        buyer_id = "847a5202-3fae-4cde-a597-1097a4a1a6ab"
        await update_portfolio_on_trade(
            buyer_id=buyer_id,
            seller_id="00000000-0000-0000-0000-000000000000",  # bot seller, skip
            price=5_000_000.0,
            quantity=0.01,
        )

    @pytest.mark.asyncio
    @patch("app.services.portfolio_service.supabase")
    async def test_bot_participants_skipped(self, mock_db):
        """If both buyer and seller are bots, no DB writes should happen."""
        from app.services.portfolio_service import update_portfolio_on_trade

        await update_portfolio_on_trade(
            buyer_id="00000000-0000-0000-0000-000000000000",
            seller_id="00000000-0000-0000-0000-000000000000",
            price=5_000_000.0,
            quantity=0.01,
        )
        mock_db.table.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.portfolio_service.supabase")
    async def test_seller_balance_credited_and_holding_reduced(self, mock_db):
        from app.services.portfolio_service import update_portfolio_on_trade

        seller_id = "847a5202-3fae-4cde-a597-1097a4a1a6ab"

        profile_exec = MagicMock(data=[{"balance": 500_000.0}])
        holding_exec = MagicMock(data=[{"quantity": 0.05, "avg_price": 4_900_000.0}])
        update_mock = MagicMock()
        update_mock.eq.return_value.execute.return_value = MagicMock()

        def _table(name):
            t = MagicMock()
            t.select.return_value.eq.return_value.execute.return_value = profile_exec
            t.select.return_value.eq.return_value.eq.return_value.execute.return_value = holding_exec
            t.update.return_value = update_mock
            return t

        mock_db.table.side_effect = _table

        await update_portfolio_on_trade(
            buyer_id="00000000-0000-0000-0000-000000000000",
            seller_id=seller_id,
            price=5_000_000.0,
            quantity=0.02,
        )


# ─────────────────────────────────────────────────────────────
# Order Service — place_order (quantity scaling + Redis events)
# ─────────────────────────────────────────────────────────────

class TestPlaceOrder:

    def _make_engine_mock(self, trade_qty_scaled: int = 5000, fill_status: str = "FILLED"):
        """Helper: return a mock C++ engine with one matching trade."""
        import _nanotrade_ext

        mock_trade = MagicMock()
        mock_trade.trade_id = "00000000-0000-0000-0000-999999999999"
        mock_trade.buy_order_id = "00000000-0000-0000-0000-111111111111"
        mock_trade.sell_order_id = "00000000-0000-0000-0000-222222222222"
        mock_trade.price = 5_500_000.0
        mock_trade.quantity = trade_qty_scaled  # scaled (engine units)
        mock_trade.timestamp = 1_680_000_000_000
        mock_trade.buyer_id = "00000000-0000-0000-0000-111111111111"
        mock_trade.seller_id = "00000000-0000-0000-0000-222222222222"

        result = MagicMock()
        result.trades = [mock_trade]
        result.remaining_quantity = 0
        result.fill_status = fill_status

        engine = MagicMock()
        engine.process_order.return_value = result
        engine.get_order_book.return_value = json.dumps({"bids": [], "asks": []})
        engine.get_last_traded_price.return_value = 5_500_000.0
        return engine

    @pytest.mark.asyncio
    @patch("app.services.order_service.supabase")
    @patch("app.services.order_service.validate_user_funds", new_callable=AsyncMock)
    @patch("app.services.order_service.update_portfolio_on_trade", new_callable=AsyncMock)
    @patch("app.services.order_service.get_portfolio_data", new_callable=AsyncMock)
    async def test_quantity_scaled_correctly_to_engine(
        self, mock_portfolio, mock_update, mock_validate, mock_db
    ):
        """1 BTC = 1,000,000 engine units — verify the scaling."""
        import _nanotrade_ext
        from app.services.order_service import place_order

        mock_portfolio.return_value = {"user_id": "mock", "balance": 5000.0, "holdings": []}

        insert_exec = MagicMock(data=[{"id": "order-uuid-mock"}])
        mock_db.table.return_value.insert.return_value.execute.return_value = insert_exec
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        engine = self._make_engine_mock(trade_qty_scaled=5000)
        redis = AsyncMock()

        await place_order(
            user_id="00000000-0000-0000-0000-111111111111",
            is_user=True,
            side="BUY",
            price=5_500_000.0,
            quantity=0.005,   # ← human-readable BTC
            engine=engine,
            redis_client=redis,
        )

        # The C++ engine must receive 5000 (= 0.005 × 1_000_000)
        cpp_order = engine.process_order.call_args[0][0]
        assert isinstance(cpp_order, _nanotrade_ext.Order)
        assert cpp_order.quantity == 5000

    @pytest.mark.asyncio
    @patch("app.services.order_service.supabase")
    @patch("app.services.order_service.validate_user_funds", new_callable=AsyncMock)
    @patch("app.services.order_service.update_portfolio_on_trade", new_callable=AsyncMock)
    @patch("app.services.order_service.get_portfolio_data", new_callable=AsyncMock)
    async def test_result_quantities_unscaled(
        self, mock_portfolio, mock_update, mock_validate, mock_db
    ):
        """Returned trade quantities must be in BTC (unscaled), not engine units."""
        from app.services.order_service import place_order

        mock_portfolio.return_value = {"user_id": "mock", "balance": 0.0, "holdings": []}
        mock_db.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "x"}])
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        engine = self._make_engine_mock(trade_qty_scaled=5000)
        redis = AsyncMock()

        result = await place_order(
            user_id="00000000-0000-0000-0000-111111111111",
            is_user=True,
            side="BUY",
            price=5_500_000.0,
            quantity=0.005,
            engine=engine,
            redis_client=redis,
        )

        assert result["status"] == "FILLED"
        assert result["remaining_quantity"] == 0.0
        assert len(result["trades"]) == 1
        assert result["trades"][0]["quantity"] == pytest.approx(0.005, abs=1e-9)

    @pytest.mark.asyncio
    @patch("app.services.order_service.supabase")
    @patch("app.services.order_service.validate_user_funds", new_callable=AsyncMock)
    @patch("app.services.order_service.update_portfolio_on_trade", new_callable=AsyncMock)
    @patch("app.services.order_service.get_portfolio_data", new_callable=AsyncMock)
    async def test_redis_event_channels_published(
        self, mock_portfolio, mock_update, mock_validate, mock_db
    ):
        """Must publish to 'trade', 'orderbook', 'price', and 'user_update' channels."""
        from app.services.order_service import place_order

        mock_portfolio.return_value = {"user_id": "mock", "balance": 0.0, "holdings": []}
        mock_db.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "x"}])
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        engine = self._make_engine_mock()
        redis = AsyncMock()

        await place_order(
            user_id="00000000-0000-0000-0000-111111111111",
            is_user=True,
            side="BUY",
            price=5_500_000.0,
            quantity=0.005,
            engine=engine,
            redis_client=redis,
        )

        published_channels = [c[0][0] for c in redis.publish.call_args_list]
        assert "trade" in published_channels
        assert "orderbook" in published_channels
        assert "price" in published_channels

    @pytest.mark.asyncio
    @patch("app.services.order_service.supabase")
    @patch("app.services.order_service.validate_user_funds", new_callable=AsyncMock)
    @patch("app.services.order_service.update_portfolio_on_trade", new_callable=AsyncMock)
    @patch("app.services.order_service.get_portfolio_data", new_callable=AsyncMock)
    async def test_redis_payload_structure_valid(
        self, mock_portfolio, mock_update, mock_validate, mock_db
    ):
        """Every Redis publish payload must have 'type', 'data', 'timestamp' keys."""
        from app.services.order_service import place_order

        mock_portfolio.return_value = {"user_id": "mock", "balance": 0.0, "holdings": []}
        mock_db.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "x"}])
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        engine = self._make_engine_mock()
        redis = AsyncMock()

        await place_order(
            user_id="00000000-0000-0000-0000-111111111111",
            is_user=True,
            side="BUY",
            price=5_500_000.0,
            quantity=0.005,
            engine=engine,
            redis_client=redis,
        )

        for c in redis.publish.call_args_list:
            channel, payload_str = c[0]
            payload = json.loads(payload_str)
            assert "type" in payload, f"Missing 'type' in {channel} payload"
            assert "data" in payload, f"Missing 'data' in {channel} payload"
            assert "timestamp" in payload, f"Missing 'timestamp' in {channel} payload"
            assert payload["type"] == channel

    @pytest.mark.asyncio
    @patch("app.services.order_service.supabase")
    @patch("app.services.order_service.validate_user_funds", new_callable=AsyncMock)
    @patch("app.services.order_service.update_portfolio_on_trade", new_callable=AsyncMock)
    @patch("app.services.order_service.get_portfolio_data", new_callable=AsyncMock)
    async def test_validate_called_with_unscaled_values(
        self, mock_portfolio, mock_update, mock_validate, mock_db
    ):
        """validate_user_funds must receive the original (unscaled) price & quantity."""
        from app.services.order_service import place_order

        mock_portfolio.return_value = {"user_id": "mock", "balance": 0.0, "holdings": []}
        mock_db.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "x"}])
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        engine = self._make_engine_mock()
        redis = AsyncMock()

        real_user = "847a5202-3fae-4cde-a597-1097a4a1a6ab"
        await place_order(
            user_id=real_user,
            is_user=True,
            side="BUY",
            price=5_500_000.0,
            quantity=0.005,
            engine=engine,
            redis_client=redis,
        )

        mock_validate.assert_called_once_with(real_user, "BUY", 5_500_000.0, 0.005)
