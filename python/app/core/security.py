import jwt
from fastapi import HTTPException, status
from app.core.config import settings

# JWK Client to retrieve public keys dynamically from Supabase (supports ES256/asymmetric verification)
jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
jwk_client = jwt.PyJWKClient(jwks_url, headers={"apikey": settings.SUPABASE_KEY})

def verify_jwt(token: str) -> dict:
    try:
        # Inspect JWT header to find the signing algorithm
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")
        
        if alg == "HS256":
            # For legacy/symmetric projects, verify using the shared JWT Secret
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False}  # Supabase aud is 'authenticated'
            )
        else:
            # For modern/asymmetric projects (ES256), verify using public key fetched from JWKS
            signing_key = jwk_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=[alg],
                options={"verify_aud": False}
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )
