from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from app.api.deps import get_current_user, get_redis_client
from app.services import portfolio_service
from app.core.config import settings

router = APIRouter()


@router.get("")
async def get_portfolio(
    current_user: dict = Depends(get_current_user),
    redis_client=Depends(get_redis_client),
):
    user_id = current_user.get("sub")
    if not user_id:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "User ID not found in token", "code": "UNAUTHORIZED"},
        )

    try:
        portfolio = await portfolio_service.get_portfolio_data(user_id)

        # Calculate unrealized PnL based on converted INR reference price
        ref_price_str = await redis_client.get(settings.REDIS_KEY_REFERENCE_PRICE)
        ref_price = float(ref_price_str) if ref_price_str else 0.0

        # Format the holdings and compute PnL using INR reference price
        for holding in portfolio["holdings"]:
            # Cast database outputs to float for security/consistency
            holding["quantity"] = float(holding["quantity"])
            holding["avg_price"] = float(holding["avg_price"])

            if holding["asset"] == "BTC" and ref_price > 0.0:
                holding["current_price"] = ref_price
                holding["pnl"] = holding["quantity"] * (
                    ref_price - holding["avg_price"]
                )
            else:
                holding["current_price"] = holding["avg_price"]
                holding["pnl"] = 0.0

        return portfolio
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": f"Failed to fetch portfolio: {str(e)}",
                "code": "PORTFOLIO_FETCH_FAILED",
            },
        )
