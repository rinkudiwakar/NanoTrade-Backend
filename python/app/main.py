import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings, _assert_required_secrets
from app.api.routes import auth, orders, portfolio, market
from app.websocket.manager import manager, redis_pubsub_listener


# Lifecycle context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    # Abort immediately if any required secret is missing or is a placeholder.
    # This prevents the server from running with invalid / leaked credentials.
    _assert_required_secrets(settings)

    # Start the background Redis listener task
    redis_task = asyncio.create_task(redis_pubsub_listener(manager))
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    redis_task.cancel()
    try:
        await redis_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
    # Disable interactive docs in production — set DOCS_URL=None via env if needed
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Reads from CORS_ORIGINS env var.  An empty list means no cross-origin
# requests are allowed, which is the safe default.
# Wildcard ("*") must be explicitly set in CORS_ORIGINS — never the default.
_cors_origins = settings.cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins if _cors_origins else [],
    allow_credentials=True,
    allow_methods=["GET", "POST"],   # only the methods we actually use
    allow_headers=["Authorization", "Content-Type"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
app.include_router(market.router, prefix="/market", tags=["market"])


@app.websocket("/ws/market")
async def websocket_market(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; handle optional client control messages
            data = await websocket.receive_text()
            await websocket.send_text(f"Received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


@app.get("/")
async def root():
    return {"message": "Welcome to NanoTrade backend API!"}
