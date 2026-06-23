"""
test_live_user.py — End-to-end integration test against a live Supabase instance.

These tests are EXCLUDED from CI (they require a real .env with valid credentials).
Run manually:
    cd python && pytest ../tests/test_live_user.py -v -m integration
"""
import sys
import os
import unittest
import pytest
import uuid
import json
from datetime import datetime, timezone

# Ensure app and build directories are in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "build")))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import supabase
from app.core.config import settings

@pytest.mark.integration
class TestLiveUserTrading(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.client = TestClient(app)
        self.test_email = f"test_trader_{uuid.uuid4().hex[:8]}@nanotrade.com"
        self.test_password = "Password123"
        self.user_id = None
        self.jwt_token = None

        print(f"\n--- Setting up live test user: {self.test_email} ---")
        try:
            # 1. Create a confirmed user using the admin API (requires service_role key)
            user_resp = supabase.auth.admin.create_user({
                "email": self.test_email,
                "password": self.test_password,
                "email_confirm": True
            })
            if not user_resp.user:
                raise Exception("Admin user creation returned empty user")
            
            self.user_id = user_resp.user.id
            print(f"User created in auth.users with ID: {self.user_id}")

            # Wait briefly for trigger execution
            import time
            time.sleep(1)

            # 2. Authenticate the user using a separate client to avoid mutating the global backend singleton
            from supabase import create_client
            temp_auth_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            
            auth_resp = temp_auth_client.auth.sign_in_with_password({
                "email": self.test_email,
                "password": self.test_password
            })
            if not auth_resp.session:
                raise Exception("Sign-in returned empty session")
            
            self.jwt_token = auth_resp.session.access_token
            self.headers = {"Authorization": f"Bearer {self.jwt_token}"}
            print("JWT token retrieved successfully.")
        except Exception as e:
            self.fail(f"Setup failed. Please check that your .env file has valid Supabase credentials (SUPABASE_KEY must be the service_role key). Error: {e}")

    async def asyncTearDown(self):
        if self.user_id:
            print(f"\n--- Cleaning up live test user: {self.test_email} ---")
            try:
                # Sign out to clear user session and restore the service_role key header
                supabase.auth.sign_out()
                
                # Delete trades associated with the test user first
                supabase.table("trades").delete().eq("buyer_id", self.user_id).execute()
                supabase.table("trades").delete().eq("seller_id", self.user_id).execute()
                
                # Delete orders associated with the test user
                supabase.table("orders").delete().eq("user_id", self.user_id).execute()
                
                # Delete user from Supabase auth (cascade will delete profile and portfolio)
                supabase.auth.admin.delete_user(self.user_id)
                print("Test user deleted from Supabase auth.")
            except Exception as e:
                print(f"Cleanup failed to delete user: {e}")

    async def test_full_trading_flow(self):
        # 1. Get Portfolio & verify profile is auto-created with default balance
        print("Checking initial portfolio...")
        response = self.client.get("/portfolio", headers=self.headers)
        self.assertEqual(response.status_code, 200, f"Portfolio fetch failed: {response.text}")
        portfolio = response.json()
        
        self.assertEqual(portfolio["user_id"], self.user_id)
        balance = float(portfolio["balance"])
        self.assertGreaterEqual(balance, 100000.00, f"Virtual balance is incorrect: {balance}")
        print(f"Profile verified. Starting Balance: INR {balance:.2f}")

        # 2. Place a BUY limit order
        # Price: INR 5,000,000.00, Quantity: 0.01 BTC (Total Cost: INR 50,000.00)
        print("Placing BUY limit order...")
        buy_payload = {
            "side": "BUY",
            "price": 5000000.00,
            "quantity": 0.01
        }
        response = self.client.post("/orders", json=buy_payload, headers=self.headers)
        self.assertEqual(response.status_code, 200, f"BUY order placement failed: {response.text}")
        buy_order_res = response.json()
        
        buy_order_id = buy_order_res["order_id"]
        self.assertEqual(buy_order_res["status"], "NEW")
        self.assertEqual(buy_order_res["remaining_quantity"], 0.01)
        print(f"BUY order placed successfully. ID: {buy_order_id}")

        # Verify order was stored in DB
        order_db = supabase.table("orders").select("*").eq("id", buy_order_id).execute().data
        self.assertTrue(order_db, "BUY order not found in Supabase orders table")
        self.assertEqual(order_db[0]["status"], "NEW")
        self.assertFalse(order_db[0]["is_bot"])

        # 3. Simulate matching SELL order from system bot
        # Price: ₹5,000,000.00, Quantity: 0.01 BTC
        print("Simulating matching SELL order from system bot...")
        sell_payload = {
            "side": "SELL",
            "price": 5000000.00,
            "quantity": 0.01
        }
        response = self.client.post("/orders/simulator", json=sell_payload)
        self.assertEqual(response.status_code, 200, f"Simulator SELL order failed: {response.text}")
        sell_order_res = response.json()
        
        self.assertEqual(sell_order_res["status"], "FILLED")
        self.assertEqual(len(sell_order_res["trades"]), 1)
        
        trade = sell_order_res["trades"][0]
        self.assertEqual(trade["buy_order_id"], buy_order_id)
        self.assertEqual(trade["price"], 5000000.00)
        self.assertEqual(trade["quantity"], 0.01)
        self.assertEqual(trade["buyer_id"], self.user_id)
        self.assertEqual(trade["seller_id"], "00000000-0000-0000-0000-000000000000")
        print(f"Match executed successfully. Trade ID: {trade['trade_id']}")

        # Verify trade was stored in DB
        trade_db = supabase.table("trades").select("*").eq("id", trade["trade_id"]).execute().data
        self.assertTrue(trade_db, "Trade record not found in Supabase trades table")
        self.assertEqual(float(trade_db[0]["price"]), 5000000.00)
        self.assertEqual(float(trade_db[0]["quantity"]), 0.01)
        self.assertTrue(trade_db[0]["is_bot_trade"])

        # Verify original BUY order status updated to FILLED in DB
        buy_order_db = supabase.table("orders").select("status", "quantity").eq("id", buy_order_id).execute().data
        self.assertEqual(buy_order_db[0]["status"], "FILLED")
        self.assertEqual(float(buy_order_db[0]["quantity"]), 0.0)

        # 4. Verify portfolio updates (deducted balance and BTC holdings credited)
        print("Verifying updated portfolio...")
        response = self.client.get("/portfolio", headers=self.headers)
        self.assertEqual(response.status_code, 200, f"Portfolio fetch failed: {response.text}")
        updated_portfolio = response.json()
        
        new_balance = float(updated_portfolio["balance"])
        expected_balance = balance - (5000000.00 * 0.01)
        self.assertAlmostEqual(new_balance, expected_balance, places=2)
        
        # Verify holding
        self.assertEqual(len(updated_portfolio["holdings"]), 1)
        holding = updated_portfolio["holdings"][0]
        self.assertEqual(holding["asset"], "BTC")
        self.assertEqual(float(holding["quantity"]), 0.01)
        self.assertEqual(float(holding["avg_price"]), 5000000.00)
        print(f"Portfolio verified successfully. New Balance: INR {new_balance:.2f}. Holdings: {holding['quantity']} BTC @ INR {holding['avg_price']:.2f}")

if __name__ == "__main__":
    unittest.main()
