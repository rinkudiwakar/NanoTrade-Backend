import sys
import os
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

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(reusable_oauth2)
) -> Dict[str, Any]:
    token = credentials.credentials
    return verify_jwt(token)

def get_matching_engine() -> _nanotrade_ext.MatchingEngine:
    return engine

async def get_redis_client() -> AsyncGenerator[redis.Redis, None]:
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()
