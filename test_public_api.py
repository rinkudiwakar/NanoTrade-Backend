import requests
import os
import time
import uuid
from supabase import create_client

API_URL = "https://sheriff-barbie-engines-beverage.trycloudflare.com"

# Load environment variables for Supabase login
from dotenv import load_dotenv
load_dotenv(".env")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def test_public_api():
    print(f"Testing public API at: {API_URL}\n")
    
    # 1. Test Health Endpoint
    print("--- 1. Testing /health ---")
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}\n")
    except Exception as e:
        print(f"Failed to reach /health: {e}\n")
        return

    # 2. Authenticate
    print("--- 2. Authenticating via Supabase ---")
    
    # We need the service role key to auto-confirm the email during testing
    import app.core.config as config
    from app.core.database import supabase as admin_supabase
    
    test_email = f"test_trader_{uuid.uuid4().hex[:8]}@nanotrade.com"
    test_password = "SecurePassword123!"
    
    try:
        print(f"Creating user: {test_email}")
        user_resp = admin_supabase.auth.admin.create_user({
            "email": test_email,
            "password": test_password,
            "email_confirm": True
        })
        time.sleep(2) # Wait for trigger to initialize profile
        
        # Login to get session token using anon key
        anon_supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        login_response = anon_supabase.auth.sign_in_with_password({"email": test_email, "password": test_password})
        token = login_response.session.access_token
        print("Successfully obtained FRESH JWT token!\n")
    except Exception as e:
        print(f"Auth failed: {e}\n")
        return
        
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # 3. Test Portfolio Endpoint
    print("--- 3. Testing /portfolio ---")
    try:
        response = requests.get(f"{API_URL}/portfolio", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Portfolio Data: {response.json()}\n")
    except Exception as e:
        print(f"Portfolio failed: {e}\n")

    # 4. Test Place Order Endpoint
    print("--- 4. Testing /orders (Placing BUY order) ---")
    try:
        payload = {
            "symbol": "BTC_USDT",
            "side": "BUY",
            "type": "LIMIT",
            "quantity": 0.01,
            "price": 60000.0
        }
        response = requests.post(f"{API_URL}/orders", headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Order Response: {response.json()}\n")
    except Exception as e:
        print(f"Order failed: {e}\n")

if __name__ == "__main__":
    test_public_api()
