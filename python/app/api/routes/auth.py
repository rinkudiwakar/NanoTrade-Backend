from fastapi import APIRouter, Depends
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/session")
async def verify_session(current_user: dict = Depends(get_current_user)):
    return {
        "status": "authenticated",
        "user_id": current_user.get("sub"),
        "email": current_user.get("email"),
        "role": current_user.get("role")
    }
