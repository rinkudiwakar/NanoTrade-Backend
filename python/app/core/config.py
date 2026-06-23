import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "NanoTrade"
    API_V1_STR: str = "/api/v1"
    
    # Supabase Settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://your-project-id.supabase.co")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "your-supabase-key")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "your-supabase-jwt-secret")
    
    # Redis Settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_KEY_USD_INR_RATE: str = "USD_INR_RATE"
    REDIS_KEY_REFERENCE_PRICE: str = "REFERENCE_PRICE"
    REDIS_KEY_LAST_TRADE_PRICE: str = "LAST_TRADE_PRICE"
    
    # Server Settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    
    class Config:
        case_sensitive = True

settings = Settings()
