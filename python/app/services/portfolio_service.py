from uuid import UUID
from app.core.database import supabase

def is_valid_uuid(val: str) -> bool:
    if not val:
        return False
    try:
        UUID(val)
        return True
    except ValueError:
        return False

async def get_portfolio_data(user_id: str) -> dict:
    """
    Fetch the portfolio data for a user including USDT balance, holdings, and current PnL.
    """
    # Fetch profile balance
    profile_resp = supabase.table("profiles").select("balance").eq("id", user_id).execute()
    balance = profile_resp.data[0]["balance"] if profile_resp.data else 0.0

    # Fetch holdings
    holdings_resp = supabase.table("portfolios").select("asset, quantity, avg_price").eq("user_id", user_id).execute()
    holdings = holdings_resp.data if holdings_resp.data else []

    return {
        "user_id": user_id,
        "balance": balance,
        "holdings": holdings
    }

async def update_portfolio_on_trade(buyer_id: str, seller_id: str, price: float, quantity: int):
    """
    Update the balances and asset holdings for both buyer and seller after a trade.
    Only updates for real users (valid UUIDs), simulator bots are skipped.
    """
    trade_value = price * quantity

    # 1. Update Buyer (if real user)
    if is_valid_uuid(buyer_id):
        # Deduct USDT balance from profile
        buyer_profile = supabase.table("profiles").select("balance").eq("id", buyer_id).execute().data
        if buyer_profile:
            new_balance = buyer_profile[0]["balance"] - trade_value
            supabase.table("profiles").update({"balance": new_balance}).eq("id", buyer_id).execute()

        # Update BTC holding
        buyer_holding = supabase.table("portfolios").select("quantity, avg_price").eq("user_id", buyer_id).eq("asset", "BTC").execute().data
        if buyer_holding:
            current_qty = buyer_holding[0]["quantity"]
            current_avg = buyer_holding[0]["avg_price"]
            new_qty = current_qty + quantity
            new_avg = ((current_qty * current_avg) + trade_value) / new_qty
            supabase.table("portfolios").update({
                "quantity": new_qty,
                "avg_price": new_avg
            }).eq("user_id", buyer_id).eq("asset", "BTC").execute()
        else:
            supabase.table("portfolios").insert({
                "user_id": buyer_id,
                "asset": "BTC",
                "quantity": quantity,
                "avg_price": price
            }).execute()

    # 2. Update Seller (if real user)
    if is_valid_uuid(seller_id):
        # Add USDT balance to profile
        seller_profile = supabase.table("profiles").select("balance").eq("id", seller_id).execute().data
        if seller_profile:
            new_balance = seller_profile[0]["balance"] + trade_value
            supabase.table("profiles").update({"balance": new_balance}).eq("id", seller_id).execute()

        # Update BTC holding
        seller_holding = supabase.table("portfolios").select("quantity, avg_price").eq("user_id", seller_id).eq("asset", "BTC").execute().data
        if seller_holding:
            current_qty = seller_holding[0]["quantity"]
            new_qty = max(0, current_qty - quantity)
            if new_qty == 0:
                # Delete holding if completely sold
                supabase.table("portfolios").delete().eq("user_id", seller_id).eq("asset", "BTC").execute()
            else:
                supabase.table("portfolios").update({
                    "quantity": new_qty
                }).eq("user_id", seller_id).eq("asset", "BTC").execute()
