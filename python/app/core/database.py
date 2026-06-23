# app/core/database.py

from app.core.config import settings

from supabase import create_client

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
