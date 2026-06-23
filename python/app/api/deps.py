import sys
import os
import asyncio
from typing import AsyncGenerator, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis.asyncio as redis

# Add build directory to path to import _nanotrade_ext
build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "build"))
if build_dir not in sys.path:
    sys.path.append(build_dir)

import _nanotrade_ext
from app.core.config import settings
from app.core.security import verify_jwt

# Instantiate global matching engine (stateful, in-process C++ object)
engine = _nanotrade_ext.MatchingEngine()

reusable_oauth2 = HTTPBearer()

# In-memory dictionary to store asyncio.Lock per user for sequential processing
user_locks = {}

def get_user_lock(user_id: str) -> asyncio.Lock:
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()
    return user_locks[user_id]

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(reusable_oauth2)
) -> Dict[str, Any]:
    token = credentials.credentials
    return verify_jwt(token)

async def get_redis_client() -> AsyncGenerator[redis.Redis, None]:
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()

async def check_rate_limit(
    current_user: Dict[str, Any] = Depends(get_current_user),
    redis_client = Depends(get_redis_client)
):
    user_id = current_user.get("sub")
    if not user_id:
        return
        
    key = f"rate_limit:{user_id}"
    requests_count = await redis_client.incr(key)
    
    if requests_count == 1:
        await redis_client.expire(key, 1)
    elif requests_count > 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded. Maximum 5 orders per second allowed.",
                "code": "RATE_LIMIT_EXCEEDED"
            }
        )

def get_matching_engine() -> _nanotrade_ext.MatchingEngine:
    return engine
