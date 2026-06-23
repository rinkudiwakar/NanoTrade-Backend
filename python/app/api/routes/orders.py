from app.api.deps import check_rate_limit, get_current_user, get_redis_client
from app.core.config import settings
from app.services import order_service
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

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


def _verify_simulator_secret(x_simulator_secret: str = Header(default="")) -> None:
    """
    Dependency that validates the shared simulator secret header.
    The Celery worker must send  X-Simulator-Secret: <SIMULATOR_SECRET>  on every
    call to POST /orders/simulator.  If SIMULATOR_SECRET is unset in .env the
    endpoint is effectively disabled (no header will ever match an empty secret).
    """
    expected = settings.SIMULATOR_SECRET
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Simulator endpoint is disabled. Set SIMULATOR_SECRET in .env.",
                "code": "SIMULATOR_DISABLED",
            },
        )
    if x_simulator_secret != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Invalid simulator secret.", "code": "FORBIDDEN"},
        )


@router.post("", dependencies=[Depends(check_rate_limit)])
async def create_user_order(
    order_in: OrderCreate,
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
        result = await order_service.place_order(
            user_id=user_id,
            is_user=True,
            side=order_in.side,
            price=order_in.price,
            quantity=order_in.quantity,
            redis_client=redis_client,
        )
        return result
    except ValueError as e:
        # Pre-execution funds / holdings validation error
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": str(e), "code": "INSUFFICIENT_FUNDS_OR_HOLDINGS"},
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": f"Order processing failed: {str(e)}",
                "code": "ORDER_PROCESSING_FAILED",
            },
        )


@router.post("/simulator", dependencies=[Depends(_verify_simulator_secret)])
async def create_simulator_order(
    order_in: OrderCreate, redis_client=Depends(get_redis_client)
):
    """
    Internal-only endpoint for the Celery market simulator.
    Requires X-Simulator-Secret header matching SIMULATOR_SECRET in .env.
    Never call this from the frontend.
    """
    bot_id = "00000000-0000-0000-0000-000000000000"
    try:
        result = await order_service.place_order(
            user_id=bot_id,
            is_user=False,
            side=order_in.side,
            price=order_in.price,
            quantity=order_in.quantity,
            redis_client=redis_client,
        )
        return result
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": f"Simulator order processing failed: {str(e)}",
                "code": "SIMULATOR_ORDER_FAILED",
            },
        )


@router.get("/history", dependencies=[Depends(check_rate_limit)])
async def get_order_history(current_user: dict = Depends(get_current_user)):
    """REST fallback for getting order history"""
    user_id = current_user.get("sub")
    if not user_id:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})

    from app.core.database import supabase

    try:
        res = (
            supabase.table("orders")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        return {"orders": res.data}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
