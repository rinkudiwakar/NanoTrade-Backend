NanoTrade/
├── include/              # C++ headers
├── src/                  # C++ implementation
├── build/
│
├── python/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── auth.py
│   │   │   │   ├── orders.py
│   │   │   │   ├── portfolio.py
│   │   │   │   └── market.py
│   │   │   └── deps.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   │
│   │   ├── db/
│   │   │   ├── models.py
│   │   │   └── session.py
│   │   │
│   │   ├── services/
│   │   │   ├── order_service.py
│   │   │   ├── portfolio_service.py
│   │   │   ├── simulator_service.py
│   │   │   └── strategy_service.py
│   │   │
│   │   ├── websocket/
│   │   │   └── manager.py
│   │   │
│   │   ├── workers/
│   │   │   ├── celery_app.py
│   │   │   └── tasks.py
│   │   │
│   │   └── main.py
│   │
│   ├── fastapi_server.py (temporary)
│   └── requirements.txt