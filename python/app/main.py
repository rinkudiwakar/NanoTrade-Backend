import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import auth, orders, portfolio, market
from app.websocket.manager import manager, redis_pubsub_listener

# Lifecycle context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background Redis listener task
    redis_task = asyncio.create_task(redis_pubsub_listener(manager))
    yield
    # Shutdown: Cancel the background Redis listener task
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
app.include_router(market.router, prefix="/market", tags=["market"])

@app.websocket("/ws/market")
async def websocket_market(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the websocket open and listen for optional control frames/messages
            data = await websocket.receive_text()
            # Respond to client messages if needed (e.g., ping/pong or subscribe commands)
            await websocket.send_text(f"Received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

@app.get("/")
async def root():
    return {"message": "Welcome to NanoTrade backend API!"}
