from typing import Any, cast
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
    Accounts for funds already locked in pending (QUEUED, PROCESSING, NEW, PARTIALLY_FILLED) orders.
    """
    if not is_valid_uuid(user_id) or user_id == "00000000-0000-0000-0000-000000000000":
        # Skip validation for simulator bots
        logger.debug(f"Fund validation skipped (bot/invalid) | user_id={user_id}")
        return

    logger.debug(
        f"Validating funds | user_id={user_id} side={side} price={price} qty={quantity}"
    )

    # Fetch pending orders to calculate locked funds
    pending_resp = (
        supabase.table("orders")
        .select("side, price, quantity, status")
        .eq("user_id", user_id)
        .in_("status", ["NEW", "QUEUED", "PROCESSING", "PARTIALLY_FILLED"])
        .execute()
    )

    locked_inr = 0.0
    locked_btc = 0.0
    if pending_resp.data:
        data = cast(Any, pending_resp.data)
        for order in data:
            # Note: For partially filled orders, the 'quantity' field in the DB should be the remaining quantity
            # OR we should track filled_quantity. To keep it simple, we assume quantity in DB is original,
            # but ideally the worker updates it to remaining. We'll use the DB quantity.
            if order["side"] == "BUY":
                locked_inr += float(order["price"]) * float(order["quantity"])
            elif order["side"] == "SELL":
                locked_btc += float(order["quantity"])

    if side == "BUY":
        cost = price * quantity
        profile_resp = (
            supabase.table("profiles").select("balance").eq("id", user_id).execute()
        )
        if not profile_resp.data:
            logger.error(
                f"Fund validation FAILED — profile not found | user_id={user_id}"
            )
            raise ValueError("User profile not found")
        balance = float(cast(Any, profile_resp.data)[0]["balance"])
        available_balance = balance - locked_inr

        logger.debug(
            f"BUY validation | user_id={user_id} cost=₹{cost:.2f} available=₹{available_balance:.2f} (locked=₹{locked_inr:.2f})"
        )
        if available_balance < cost:
            logger.warning(
                f"INSUFFICIENT BALANCE | user_id={user_id} required=₹{cost:.2f} available=₹{available_balance:.2f}"
            )
            raise ValueError(
                f"Insufficient balance. Required: ₹{cost:.2f}, Available: ₹{available_balance:.2f}"
            )
        logger.debug(f"BUY validation PASSED | user_id={user_id}")

    elif side == "SELL":
        portfolio_resp = (
            supabase.table("portfolios")
            .select("quantity")
            .eq("user_id", user_id)
            .eq("asset", "BTC")
            .execute()
        )
        holding_qty = (
            float(cast(Any, portfolio_resp.data)[0]["quantity"]) if portfolio_resp.data else 0.0
        )
        available_btc = holding_qty - locked_btc

        logger.debug(
            f"SELL validation | user_id={user_id} required={quantity:.6f} available={available_btc:.6f} (locked={locked_btc:.6f})"
        )
        if available_btc < quantity:
            logger.warning(
                f"INSUFFICIENT BTC | user_id={user_id} required={quantity:.6f} available={available_btc:.6f}"
            )
            raise ValueError(
                f"Insufficient BTC holdings. Required: {quantity:.6f} BTC, Available: {available_btc:.6f} BTC"
            )
        logger.debug(f"SELL validation PASSED | user_id={user_id}")


async def get_portfolio_data(user_id: str) -> dict:
    """
    Fetch the portfolio data for a user including INR balance, holdings, and current PnL.
    """
    logger.debug(f"Fetching portfolio | user_id={user_id}")

    # Fetch profile balance
    profile_resp = (
        supabase.table("profiles").select("balance").eq("id", user_id).execute()
    )
    balance = cast(Any, profile_resp.data)[0]["balance"] if profile_resp.data else 0.0

    # Fetch holdings
    holdings_resp = (
        supabase.table("portfolios")
        .select("asset, quantity, avg_price")
        .eq("user_id", user_id)
        .execute()
    )
    holdings = cast(Any, holdings_resp.data) if holdings_resp.data else []

    logger.debug(
        f"Portfolio fetched | user_id={user_id} balance=₹{float(balance):.2f} holdings={len(holdings)}"
    )
    return {"user_id": user_id, "balance": balance, "holdings": holdings}


# update_portfolio_on_trade has been removed.
# Trade settlement is now handled exclusively by the Supabase RPC `settle_trade_atomic`.
