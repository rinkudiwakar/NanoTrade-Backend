from uuid import UUID
from app.core.database import supabase
from app.core.logger import get_logger

logger = get_logger(__name__)


def is_valid_uuid(val: str) -> bool:
    if not val:
        return False
    try:
        UUID(val)
        return True
    except ValueError:
        return False


async def validate_user_funds(user_id: str, side: str, price: float, quantity: float):
    """
    Validate that the user has sufficient funds (for BUY) or sufficient assets (for SELL)
    before processing the order.
    """
    if not is_valid_uuid(user_id) or user_id == "00000000-0000-0000-0000-000000000000":
        # Skip validation for simulator bots
        logger.debug(f"Fund validation skipped (bot/invalid) | user_id={user_id}")
        return

    logger.debug(f"Validating funds | user_id={user_id} side={side} price={price} qty={quantity}")

    if side == "BUY":
        cost = price * quantity
        profile_resp = supabase.table("profiles").select("balance").eq("id", user_id).execute()
        if not profile_resp.data:
            logger.error(f"Fund validation FAILED — profile not found | user_id={user_id}")
            raise ValueError("User profile not found")
        balance = float(profile_resp.data[0]["balance"])
        logger.debug(f"BUY validation | user_id={user_id} cost=₹{cost:.2f} balance=₹{balance:.2f}")
        if balance < cost:
            logger.warning(f"INSUFFICIENT BALANCE | user_id={user_id} required=₹{cost:.2f} available=₹{balance:.2f}")
            raise ValueError(f"Insufficient balance. Required: ₹{cost:.2f}, Available: ₹{balance:.2f}")
        logger.debug(f"BUY validation PASSED | user_id={user_id}")

    elif side == "SELL":
        portfolio_resp = supabase.table("portfolios").select("quantity").eq("user_id", user_id).eq("asset", "BTC").execute()
        holding_qty = float(portfolio_resp.data[0]["quantity"]) if portfolio_resp.data else 0.0
        logger.debug(f"SELL validation | user_id={user_id} required={quantity:.6f} holding={holding_qty:.6f}")
        if holding_qty < quantity:
            logger.warning(f"INSUFFICIENT BTC | user_id={user_id} required={quantity:.6f} holding={holding_qty:.6f}")
            raise ValueError(f"Insufficient BTC holdings. Required: {quantity:.6f} BTC, Available: {holding_qty:.6f} BTC")
        logger.debug(f"SELL validation PASSED | user_id={user_id}")


async def get_portfolio_data(user_id: str) -> dict:
    """
    Fetch the portfolio data for a user including INR balance, holdings, and current PnL.
    """
    logger.debug(f"Fetching portfolio | user_id={user_id}")

    # Fetch profile balance
    profile_resp = supabase.table("profiles").select("balance").eq("id", user_id).execute()
    balance = profile_resp.data[0]["balance"] if profile_resp.data else 0.0

    # Fetch holdings
    holdings_resp = supabase.table("portfolios").select("asset, quantity, avg_price").eq("user_id", user_id).execute()
    holdings = holdings_resp.data if holdings_resp.data else []

    logger.debug(f"Portfolio fetched | user_id={user_id} balance=₹{float(balance):.2f} holdings={len(holdings)}")
    return {
        "user_id": user_id,
        "balance": balance,
        "holdings": holdings
    }


async def update_portfolio_on_trade(buyer_id: str, seller_id: str, price: float, quantity: float):
    """
    Update the balances and asset holdings for both buyer and seller after a trade.
    Only updates for real users (valid UUIDs), simulator bots are skipped.
    """
    trade_value = round(price * quantity, 2)
    logger.debug(f"update_portfolio_on_trade | buyer={buyer_id[:8]}... seller={seller_id[:8]}... price={price} qty={quantity:.6f} value=₹{trade_value:.2f}")

    # 1. Update Buyer (if real user and not system bot)
    if is_valid_uuid(buyer_id) and buyer_id != "00000000-0000-0000-0000-000000000000":
        # Deduct INR balance from profile
        buyer_profile = supabase.table("profiles").select("balance").eq("id", buyer_id).execute().data
        if buyer_profile:
            old_balance = float(buyer_profile[0]["balance"])
            new_balance = round(old_balance - trade_value, 2)
            supabase.table("profiles").update({"balance": new_balance}).eq("id", buyer_id).execute()
            logger.info(f"BUYER balance updated | user_id={buyer_id[:8]}... old=₹{old_balance:.2f} new=₹{new_balance:.2f}")
        else:
            logger.warning(f"Buyer profile not found for balance update | user_id={buyer_id}")

        # Update BTC holding
        buyer_holding = supabase.table("portfolios").select("quantity, avg_price").eq("user_id", buyer_id).eq("asset", "BTC").execute().data
        if buyer_holding:
            current_qty = float(buyer_holding[0]["quantity"])
            current_avg = float(buyer_holding[0]["avg_price"])
            new_qty = round(current_qty + quantity, 6)
            new_avg = round(((current_qty * current_avg) + trade_value) / new_qty, 2)
            supabase.table("portfolios").update({
                "quantity": new_qty,
                "avg_price": new_avg
            }).eq("user_id", buyer_id).eq("asset", "BTC").execute()
            logger.info(f"BUYER BTC holding updated | user_id={buyer_id[:8]}... old_qty={current_qty:.6f} new_qty={new_qty:.6f} avg_price=₹{new_avg:.2f}")
        else:
            supabase.table("portfolios").insert({
                "user_id": buyer_id,
                "asset": "BTC",
                "quantity": quantity,
                "avg_price": price
            }).execute()
            logger.info(f"BUYER BTC holding created | user_id={buyer_id[:8]}... qty={quantity:.6f} avg_price=₹{price:.2f}")
    else:
        logger.debug(f"Buyer is bot/invalid — skipping portfolio update | buyer_id={buyer_id}")

    # 2. Update Seller (if real user and not system bot)
    if is_valid_uuid(seller_id) and seller_id != "00000000-0000-0000-0000-000000000000":
        # Add INR balance to profile
        seller_profile = supabase.table("profiles").select("balance").eq("id", seller_id).execute().data
        if seller_profile:
            old_balance = float(seller_profile[0]["balance"])
            new_balance = round(old_balance + trade_value, 2)
            supabase.table("profiles").update({"balance": new_balance}).eq("id", seller_id).execute()
            logger.info(f"SELLER balance updated | user_id={seller_id[:8]}... old=₹{old_balance:.2f} new=₹{new_balance:.2f}")
        else:
            logger.warning(f"Seller profile not found for balance update | user_id={seller_id}")

        # Update BTC holding
        seller_holding = supabase.table("portfolios").select("quantity, avg_price").eq("user_id", seller_id).eq("asset", "BTC").execute().data
        if seller_holding:
            current_qty = float(seller_holding[0]["quantity"])
            new_qty = round(max(0.0, current_qty - quantity), 6)
            if new_qty < 1e-6:
                # Delete holding if completely sold (under precision limit of 6 decimals)
                supabase.table("portfolios").delete().eq("user_id", seller_id).eq("asset", "BTC").execute()
                logger.info(f"SELLER BTC holding deleted (fully sold) | user_id={seller_id[:8]}...")
            else:
                supabase.table("portfolios").update({
                    "quantity": new_qty
                }).eq("user_id", seller_id).eq("asset", "BTC").execute()
                logger.info(f"SELLER BTC holding updated | user_id={seller_id[:8]}... old_qty={current_qty:.6f} new_qty={new_qty:.6f}")
        else:
            logger.warning(f"SELLER has no BTC holding to reduce | user_id={seller_id}")
    else:
        logger.debug(f"Seller is bot/invalid — skipping portfolio update | seller_id={seller_id}")
