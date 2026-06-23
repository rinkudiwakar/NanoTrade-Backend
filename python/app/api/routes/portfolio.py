from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user, get_redis_client
from app.services import portfolio_service

router = APIRouter()

@router.get("")
async def get_portfolio(
    current_user: dict = Depends(get_current_user),
    redis_client = Depends(get_redis_client)
):
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")
        
    try:
        portfolio = await portfolio_service.get_portfolio_data(user_id)
        
        # Calculate unrealized PnL based on Binance reference price
        ref_price_str = await redis_client.get("binance_price")
        ref_price = float(ref_price_str) if ref_price_str else 0.0
        
        for holding in portfolio["holdings"]:
            if holding["asset"] == "BTC" and ref_price > 0.0:
                holding["current_price"] = ref_price
                holding["pnl"] = holding["quantity"] * (ref_price - holding["avg_price"])
            else:
                holding["current_price"] = holding["avg_price"]
                holding["pnl"] = 0.0
                
        return portfolio
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch portfolio: {str(e)}")
