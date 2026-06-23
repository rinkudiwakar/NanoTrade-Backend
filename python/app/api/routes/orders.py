from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.api.deps import get_current_user, get_matching_engine, get_redis_client
from app.services import order_service

router = APIRouter()

class OrderCreate(BaseModel):
    side: str = Field(..., pattern="^(BUY|SELL)$")
    price: float = Field(..., gt=0.0)
    quantity: int = Field(..., gt=0)

@router.post("")
async def create_user_order(
    order_in: OrderCreate,
    current_user: dict = Depends(get_current_user),
    engine = Depends(get_matching_engine),
    redis_client = Depends(get_redis_client)
):
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")
        
    try:
        result = await order_service.place_order(
            user_id=user_id,
            is_user=True,
            side=order_in.side,
            price=order_in.price,
            quantity=order_in.quantity,
            engine=engine,
            redis_client=redis_client
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order processing failed: {str(e)}")

@router.post("/simulator")
async def create_simulator_order(
    order_in: OrderCreate,
    engine = Depends(get_matching_engine),
    redis_client = Depends(get_redis_client)
):
    # Simulator orders are marked as is_user=False and have a bot ID
    bot_id = "bot_simulator"
    try:
        result = await order_service.place_order(
            user_id=bot_id,
            is_user=False,
            side=order_in.side,
            price=order_in.price,
            quantity=order_in.quantity,
            engine=engine,
            redis_client=redis_client
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulator order processing failed: {str(e)}")

