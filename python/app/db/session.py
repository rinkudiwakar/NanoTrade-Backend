"""
app/db/session.py

Supabase client session helpers.
Provides a single shared Supabase client and a helper to get it as a FastAPI dependency.

Architecture rule: Only FastAPI (not C++ engine) ever touches the DB.
"""

from supabase import Client
from app.core.database import supabase as _supabase_client


def get_supabase() -> Client:
    """
    Returns the shared Supabase client instance.
    Can be used as a FastAPI dependency:

        from app.db.session import get_supabase
        from fastapi import Depends

        @router.get("/something")
        async def handler(db: Client = Depends(get_supabase)):
            ...
    """
    return _supabase_client


# Convenience alias for direct imports
supabase: Client = _supabase_client
