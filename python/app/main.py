import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings, _assert_required_secrets
from app.core.logger import get_logger
from app.api.routes import auth, orders, portfolio, market
from app.websocket.manager import manager, redis_pubsub_listener

logger = get_logger(__name__)


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
    lifespan=lifespan
)

# Set CORS origins
if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Fallback to wildcard for local dev if not specified
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(auth.router,      prefix="/auth",      tags=["auth"])
app.include_router(orders.router,    prefix="/orders",    tags=["orders"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
app.include_router(market.router,    prefix="/market",    tags=["market"])


@app.websocket("/ws/market")
async def websocket_market(websocket: WebSocket):
    await manager.connect(websocket)
    client = websocket.client
    logger.info(f"WebSocket connected | client={client}")
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"WebSocket message received | data={data}")
            await websocket.send_text(f"Received: {data}")
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected | client={client}")
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket error | client={client} error={e}")
        manager.disconnect(websocket)


@app.get("/")
async def root():
    return {"message": "Welcome to NanoTrade backend API!"}


@app.get("/health")
async def health():
    logger.debug("Health check called")
    return {"status": "ok", "service": settings.PROJECT_NAME}
