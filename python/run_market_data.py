import asyncio
from app.market_data import market_data_listener
from app.core.logger import setup_logging
from app.core.config import settings

if __name__ == "__main__":
    setup_logging(log_level=settings.LOG_LEVEL)
    asyncio.run(market_data_listener())
