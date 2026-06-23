import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

IS_CI = os.getenv("CI") == "true"

# =========================
# 🔥 FORCE LOAD .env (ABSOLUTE PATH)
# =========================

# Get project root → NanoTrade/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Path to .env inside python/
ENV_PATH = os.path.join(BASE_DIR, ".env")

# Load environment variables
load_dotenv(dotenv_path=ENV_PATH)



# =========================
# SETTINGS CLASS
# =========================

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,            # 🔥 absolute path
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # ── Project ─────────────────────────────
    PROJECT_NAME: str = "NanoTrade"
    API_V1_STR: str = "/api/v1"

    # ── Supabase (REQUIRED) ────────────────
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_JWT_SECRET: str

    # ── Redis ──────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_KEY_USD_INR_RATE: str = "USD_INR_RATE"
    REDIS_KEY_REFERENCE_PRICE: str = "REFERENCE_PRICE"
    REDIS_KEY_LAST_TRADE_PRICE: str = "LAST_TRADE_PRICE"

    # ── Server ─────────────────────────────
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # ── CORS ───────────────────────────────
    CORS_ORIGINS: str = ""

    # ── Simulator Secret ───────────────────
    SIMULATOR_SECRET: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.CORS_ORIGINS.strip():
            return []
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


# =========================
# 🔒 SECURITY CHECK
# =========================

def _assert_required_secrets(s: "Settings") -> None:
    if os.getenv("CI") == "true":
        return  # 🔥 skip strict checks in CI

    checks = {
        "SUPABASE_URL": s.SUPABASE_URL,
        "SUPABASE_KEY": s.SUPABASE_KEY,
        "SUPABASE_JWT_SECRET": s.SUPABASE_JWT_SECRET,
    }

    for name, value in checks.items():
        if not value or value.strip() == "":
            raise RuntimeError(
                f"[Security] {name} is not configured."
            )

# =========================
# INIT SETTINGS
# =========================

settings = Settings()