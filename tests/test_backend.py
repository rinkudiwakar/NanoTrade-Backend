import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os
import json

# Ensure python directory is in system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python")))
# Ensure build directory is in system path for C++ bindings
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "build")))

class TestNanoTradeBackend(unittest.IsolatedAsyncioTestCase):
    
    @patch("app.services.portfolio_service.supabase")
    async def test_validate_user_funds_buy_insufficient(self, mock_db):
        from app.services.portfolio_service import validate_user_funds
        
        # Mock user balance response from Supabase
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[{"balance": 1000.00}])
        mock_db.table.return_value.select.return_value.eq.return_value = mock_execute
        
        # Test BUY order requiring ₹1200.00 (100 * 12) -> should fail
        with self.assertRaises(ValueError) as context:
            await validate_user_funds(
                user_id="847a5202-3fae-4cde-a597-1097a4a1a6ab", 
                side="BUY", 
                price=100.0, 
                quantity=12.0
            )
        self.assertIn("Insufficient balance", str(context.exception))

    @patch("app.services.portfolio_service.supabase")
    async def test_validate_user_funds_buy_sufficient(self, mock_db):
        from app.services.portfolio_service import validate_user_funds
        
        # Mock user balance response from Supabase
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[{"balance": 5000.00}])
        mock_db.table.return_value.select.return_value.eq.return_value = mock_execute
        
        # Test BUY order requiring ₹4500.00 (900 * 5) -> should succeed without error
        try:
            await validate_user_funds(
                user_id="847a5202-3fae-4cde-a597-1097a4a1a6ab", 
                side="BUY", 
                price=900.0, 
                quantity=5.0
            )
        except ValueError:
            self.fail("validate_user_funds raised ValueError unexpectedly!")

    @patch("app.services.portfolio_service.supabase")
    async def test_validate_user_funds_sell_insufficient(self, mock_db):
        from app.services.portfolio_service import validate_user_funds
        
        # Mock BTC holdings from Supabase (user has 0.005 BTC)
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[{"quantity": 0.005}])
        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value = mock_execute
        
        # Test SELL order requiring 0.01 BTC -> should fail
        with self.assertRaises(ValueError) as context:
            await validate_user_funds(
                user_id="847a5202-3fae-4cde-a597-1097a4a1a6ab", 
                side="SELL", 
                price=5500000.0, 
                quantity=0.01
            )
        self.assertIn("Insufficient BTC holdings", str(context.exception))

    @patch("app.services.portfolio_service.supabase")
    async def test_validate_user_funds_sell_sufficient(self, mock_db):
        from app.services.portfolio_service import validate_user_funds
        
        # Mock BTC holdings from Supabase (user has 0.05 BTC)
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[{"quantity": 0.05}])
        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value = mock_execute
        
        # Test SELL order requiring 0.02 BTC -> should succeed without error
        try:
            await validate_user_funds(
                user_id="847a5202-3fae-4cde-a597-1097a4a1a6ab", 
                side="SELL", 
                price=5500000.0, 
                quantity=0.02
            )
        except ValueError:
            self.fail("validate_user_funds raised ValueError unexpectedly!")

    @patch("app.services.order_service.supabase")
    @patch("app.services.order_service.validate_user_funds")
    @patch("app.services.order_service.update_portfolio_on_trade")
    @patch("app.services.order_service.get_portfolio_data")
    async def test_place_order_scaling_and_events(self, mock_get_port, mock_update_port, mock_val_funds, mock_db):
        from app.services.order_service import place_order
        import _nanotrade_ext
        
        # Mock get_portfolio_data response
        mock_get_port.return_value = {"user_id": "mock", "balance": 5000.0, "holdings": []}
        
        # Mock database insert response
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[{"id": "order-uuid-mock"}])
        mock_db.table.return_value.insert.return_value = mock_execute
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_db.table.return_value.update.return_value.eq.return_value = mock_execute
        
        # Mock C++ engine result
        mock_engine = MagicMock()
        # Mock an incoming trade from C++
        mock_cpp_trade = MagicMock()
        mock_cpp_trade.trade_id = "00000000-0000-0000-0000-999999999999"
        mock_cpp_trade.buy_order_id = "00000000-0000-0000-0000-111111111111"
        mock_cpp_trade.sell_order_id = "00000000-0000-0000-0000-222222222222"
        mock_cpp_trade.price = 5500000.0
        mock_cpp_trade.quantity = 5000  # representing 0.005 BTC scaled by 1,000,000
        mock_cpp_trade.timestamp = 1680000000000
        mock_cpp_trade.buyer_id = "00000000-0000-0000-0000-111111111111"
        mock_cpp_trade.seller_id = "00000000-0000-0000-0000-222222222222"
        
        mock_result = MagicMock()
        mock_result.trades = [mock_cpp_trade]
        mock_result.remaining_quantity = 0
        mock_result.fill_status = "FILLED"
        
        mock_engine.process_order.return_value = mock_result
        mock_engine.get_order_book.return_value = '{"bids": [], "asks": []}'
        mock_engine.get_last_traded_price.return_value = 5500000.0
        
        # Mock Redis client
        mock_redis = AsyncMock()
        
        # Call place_order with unscaled quantity 0.005
        res = await place_order(
            user_id="00000000-0000-0000-0000-111111111111",
            is_user=True,
            side="BUY",
            price=5500000.0,
            quantity=0.005,
            engine=mock_engine,
            redis_client=mock_redis
        )
        
        # Verify result contains the expected fields and values
        self.assertEqual(res["status"], "FILLED")
        self.assertEqual(res["remaining_quantity"], 0.0)
        self.assertEqual(len(res["trades"]), 1)
        self.assertEqual(res["trades"][0]["quantity"], 0.005)  # Unscaled
        
        # Verify that validate_user_funds was called with unscaled values
        mock_val_funds.assert_called_once_with("00000000-0000-0000-0000-111111111111", "BUY", 5500000.0, 0.005)
        
        # Verify that the C++ Order was instantiated with scaled quantity (5000)
        args, kwargs = mock_engine.process_order.call_args
        cpp_order_arg = args[0]
        self.assertIsInstance(cpp_order_arg, _nanotrade_ext.Order)
        self.assertEqual(cpp_order_arg.quantity, 5000)  # scaled!
        
        # Verify standard event structure published to Redis
        # redis_client.publish should be called for "trade", "orderbook", "price", and "user_update"
        pub_calls = mock_redis.publish.call_args_list
        channels = [call[0][0] for call in pub_calls]
        self.assertIn("trade", channels)
        self.assertIn("orderbook", channels)
        self.assertIn("price", channels)
        self.assertIn("user_update", channels)
        
        # Check payload format of the "trade" event
        for call in pub_calls:
            channel, payload_str = call[0][0], call[0][1]
            payload = json.loads(payload_str)
            self.assertIn("type", payload)
            self.assertIn("data", payload)
            self.assertIn("timestamp", payload)
            self.assertEqual(payload["type"], channel)

if __name__ == "__main__":
    unittest.main()
