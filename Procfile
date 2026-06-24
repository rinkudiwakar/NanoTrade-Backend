web: cd python && uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: cd python && celery -A app.workers.celery_app worker --loglevel=info
engine: cd python && python -m app.workers.engine_daemon
