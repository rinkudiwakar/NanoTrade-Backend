import json

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.api.deps import get_redis_client
from app.core.config import settings
from app.core.database import supabase

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /market/orderbook
# Returns the current C++ engine order book (bids and asks in INR/BTC)
# ---------------------------------------------------------------------------


@router.get("/orderbook")
async def get_orderbook(redis_client=Depends(get_redis_client)):
    """
    Returns the live order book.
    Quantities are unscaled from engine units (10^6) back to BTC (6 decimals).
    """
    try:
        book_json_str = await redis_client.get("engine:orderbook")
        if not book_json_str:
            return {"bids": [], "asks": []}

        parsed_orderbook = json.loads(book_json_str)

        # Unscale quantities: engine stores 1 BTC as 1,000,000 units
        if isinstance(parsed_orderbook, dict):
            for side_name in ["bids", "asks"]:
                if side_name in parsed_orderbook:
                    for entry in parsed_orderbook[side_name]:
                        if "quantity" in entry:
                            entry["quantity"] = round(entry["quantity"] / 1_000_000, 6)

        return parsed_orderbook
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": f"Failed to get orderbook: {str(e)}",
                "code": "ORDERBOOK_FETCH_FAILED",
            },
        )


# ---------------------------------------------------------------------------
# GET /market/price
# Returns current reference price (from Binance via Redis) and last engine trade price
# ---------------------------------------------------------------------------


@router.get("/price")
async def get_price(redis_client=Depends(get_redis_client)):
    """
    Returns:
    - reference_price_inr: Binance BTC/USDT converted to INR (used for simulation anchoring)
    - usd_inr_rate: Cached FX rate used for conversion
    - last_traded_price_inr: Last price at which a trade was matched by the C++ engine

    ARCHITECTURE RULE: reference_price is ONLY an anchor for the simulator.
    The engine's last_traded_price is the actual price shown in the frontend.
    """
    try:
        # Read from Redis cache (populated by Celery tasks)
        ref_price_str = await redis_client.get(settings.REDIS_KEY_REFERENCE_PRICE)
        usd_inr_str = await redis_client.get(settings.REDIS_KEY_USD_INR_RATE)
        last_traded_str = await redis_client.get(settings.REDIS_KEY_LAST_TRADE_PRICE)

        ref_price = float(ref_price_str) if ref_price_str else None
        usd_inr_rate = float(usd_inr_str) if usd_inr_str else None
        last_traded = float(last_traded_str) if last_traded_str else None

        # Derive USD price from INR and FX rate if available
        binance_usd = None
        if ref_price and usd_inr_rate and usd_inr_rate > 0:
            binance_usd = round(ref_price / usd_inr_rate, 2)

        return {
            "binance_price_usd": binance_usd,
            "usd_inr_rate": usd_inr_rate,
            "reference_price_inr": ref_price,
            "last_traded_price_inr": last_traded,
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": f"Failed to get price data: {str(e)}",
                "code": "PRICE_FETCH_FAILED",
            },
        )


# ---------------------------------------------------------------------------
# GET /market/trades
# Returns the most recent trades from Supabase (public feed)
# ---------------------------------------------------------------------------


@router.get("/trades")
async def get_recent_trades(limit: int = 50):
    """
    Returns the most recent N trades from the Supabase trades table.
    Excludes bot-only internal trades from the public feed.
    Default limit: 50 trades. Max: 200.
    """
    try:
        # Cap limit to prevent abuse
        limit = min(limit, 200)

        resp = (
            supabase.table("trades")
            .select("id, price, quantity, buyer_id, seller_id, created_at")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        from typing import Any, cast
        trades = cast(Any, resp.data) if resp.data else []

        # Format for frontend — hide internal bot UUIDs from the public feed
        BOT_ID = "00000000-0000-0000-0000-000000000000"
        formatted = []
        for t in trades:
            formatted.append(
                {
                    "id": t["id"],
                    "price": float(t["price"]),
                    "quantity": float(t["quantity"]),
                    "buyer_is_user": t["buyer_id"] != BOT_ID,
                    "seller_is_user": t["seller_id"] != BOT_ID,
                    "created_at": t["created_at"],
                }
            )

        return {"trades": formatted, "count": len(formatted)}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": f"Failed to fetch trades: {str(e)}",
                "code": "TRADES_FETCH_FAILED",
            },
        )
