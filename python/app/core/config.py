import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Configure Pydantic to read from a .env file if it exists, falling back to OS env vars
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    PROJECT_NAME: str = "NanoTrade"
    API_V1_STR: str = "/api/v1"
    
    # Supabase Settings (FastAPI requires service_role key to write/bypass RLS)
    SUPABASE_URL: str = "https://your-project-id.supabase.co"
    SUPABASE_KEY: str = "your-supabase-service-role-key"
    SUPABASE_JWT_SECRET: str = "your-supabase-jwt-secret"
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_KEY_USD_INR_RATE: str = "USD_INR_RATE"
    REDIS_KEY_REFERENCE_PRICE: str = "REFERENCE_PRICE"
    REDIS_KEY_LAST_TRADE_PRICE: str = "LAST_TRADE_PRICE"
    
    # Server Settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000

settings = Settings()
