import jwt
from app.core.config import settings
from app.core.logger import get_logger
from fastapi import HTTPException, status

logger = get_logger(__name__)

# JWK Client to retrieve public keys dynamically from Supabase (supports ES256/asymmetric verification)
jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
logger.info(f"Initializing JWK client | jwks_url={jwks_url}")
jwk_client = jwt.PyJWKClient(jwks_url, headers={"apikey": settings.SUPABASE_KEY})


def verify_jwt(token: str) -> dict:
    try:
        # Inspect JWT header to find the signing algorithm
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")
        logger.debug(f"JWT header parsed | alg={alg}")

        if alg == "HS256":
            # For legacy/symmetric projects, verify using the shared JWT Secret
            logger.debug("Verifying JWT with HS256 (symmetric secret)")
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},  # Supabase aud is 'authenticated'
            )
        else:
            # For modern/asymmetric projects (ES256), verify using public key fetched from JWKS
            logger.debug(f"Verifying JWT with {alg} (JWKS public key)")
            signing_key = jwk_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token, signing_key.key, algorithms=[alg], options={"verify_aud": False}
            )

        user_id = payload.get("sub", "unknown")
        role = payload.get("role", "unknown")
        logger.debug(f"JWT verified OK | user_id={user_id} role={role} alg={alg}")
        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("JWT verification failed | reason=token_expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"JWT verification failed | reason=invalid_token error={e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )
