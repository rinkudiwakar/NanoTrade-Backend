from celery import Celery
from celery.signals import worker_ready

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

celery_app = Celery(
    "nanotrade_workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

# Celery Configurations
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
)

@worker_ready.connect
def at_start(sender, **k):
    logger.info("Worker is ready! Sending daemon tasks to the queue...")
    with sender.app.connection() as conn:
        sender.app.send_task("app.workers.tasks.run_fx_converter", connection=conn)
        sender.app.send_task("app.workers.tasks.run_binance_feed", connection=conn)
        sender.app.send_task("app.workers.tasks.run_market_simulator", connection=conn)

if __name__ == "__main__":
    celery_app.start()
