from typing import Any, AsyncGenerator, Dict

import redis.asyncio as redis
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.logger import get_logger
from app.core.security import verify_jwt

logger = get_logger(__name__)

reusable_oauth2 = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
) -> Dict[str, Any]:
    if not credentials:
        return (
            {}
        )  # Allow unauthenticated requests to pass through to check_rate_limit for IP based limiting, but endpoints will reject if user is required.
    token = credentials.credentials
    logger.debug("Verifying JWT token")
    try:
        payload = verify_jwt(token)
        user_id = payload.get("sub", "unknown")
        logger.debug(f"JWT verified | user_id={user_id}")
        return payload
    except Exception as e:
        logger.warning(f"JWT verification failed | error={e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_redis_client() -> AsyncGenerator[redis.Redis, None]:
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


async def check_rate_limit(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    """
    Atomic rate limiting via Redis Pipeline.
    Strict limits for POST/PUT (e.g., 5 req/sec).
    Relaxed limits for GET (e.g., 20 req/sec).
    Applied per user_id if authenticated, otherwise per IP.
    """
    user_id = current_user.get("sub")
    client_ip = request.client.host if request.client else "unknown_ip"

    identifier = f"user:{user_id}" if user_id else f"ip:{client_ip}"
    method = request.method

    if method in ["POST", "PUT", "DELETE"]:
        max_requests = 5
        window_seconds = 1
        key = f"rate_limit:strict:{identifier}"
    else:
        max_requests = 20
        window_seconds = 1
        key = f"rate_limit:relaxed:{identifier}"

    # Atomic INCR + EXPIRE via pipeline
    async with redis_client.pipeline(transaction=True) as pipe:
        pipe.incr(key)
        pipe.expire(key, window_seconds, nx=True)
        results = await pipe.execute()

    requests_count = results[0]

    if requests_count > max_requests:
        logger.warning(
            f"Rate limit exceeded | method={method} identifier={identifier} count={requests_count}/{max_requests}"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} second(s) allowed.",
                "code": "RATE_LIMIT_EXCEEDED",
            },
        )
    else:
        logger.debug(
            f"Rate limit check passed | method={method} identifier={identifier} count={requests_count}/{max_requests}"
        )
