from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from app.api.deps import get_current_user, get_matching_engine, get_redis_client, check_rate_limit
from app.services import order_service

router = APIRouter()

class OrderCreate(BaseModel):
    side: str = Field(..., pattern="^(BUY|SELL)$")
    price: float = Field(..., gt=0.0)
    quantity: float = Field(..., gt=0.0)

    @field_validator("price")
    @classmethod
    def validate_price_precision(cls, v: float) -> float:
        if abs(round(v, 2) - v) > 1e-9:
            raise ValueError("Price precision cannot exceed 2 decimal places")
        return round(v, 2)

    @field_validator("quantity")
    @classmethod
    def validate_quantity_precision(cls, v: float) -> float:
        if abs(round(v, 6) - v) > 1e-9:
            raise ValueError("Quantity precision cannot exceed 6 decimal places")
        return round(v, 6)

@router.post("", dependencies=[Depends(check_rate_limit)])
async def create_user_order(
    order_in: OrderCreate,
    current_user: dict = Depends(get_current_user),
    engine = Depends(get_matching_engine),
    redis_client = Depends(get_redis_client)
):
    user_id = current_user.get("sub")
    if not user_id:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "User ID not found in token", "code": "UNAUTHORIZED"}
        )
        
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
    except ValueError as e:
        # Pre-execution funds validation error
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": str(e), "code": "INSUFFICIENT_FUNDS_OR_HOLDINGS"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Order processing failed: {str(e)}", "code": "ORDER_PROCESSING_FAILED"}
        )

@router.post("/simulator")
async def create_simulator_order(
    order_in: OrderCreate,
    engine = Depends(get_matching_engine),
    redis_client = Depends(get_redis_client)
):
    # Simulator orders use the dedicated system bot UUID
    bot_id = "00000000-0000-0000-0000-000000000000"
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
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Simulator order processing failed: {str(e)}", "code": "SIMULATOR_ORDER_FAILED"}
        )
