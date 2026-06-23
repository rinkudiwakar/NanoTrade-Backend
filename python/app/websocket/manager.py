import asyncio
import json
from typing import List
from fastapi import WebSocket
import redis.asyncio as redis
from app.core.config import settings

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # Connection might be dead, handled on disconnect
                pass

manager = ConnectionManager()

async def redis_pubsub_listener(connection_manager: ConnectionManager):
    """
    Subscribes to Redis channels and broadcasts messages to all connected WebSockets.
    """
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe("trades", "orderbook")
    
    try:
        async for message in pubsub.listen():
            if message and message.get("type") == "message":
                channel = message.get("channel")
                data = message.get("data")
                
                try:
                    parsed_data = json.loads(data)
                except Exception:
                    parsed_data = data
                
                payload = {
                    "event": channel, # e.g., "trades" or "orderbook"
                    "data": parsed_data
                }
                
                await connection_manager.broadcast(json.dumps(payload))
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"WebSocket Redis listener encountered error: {e}")
    finally:
        await pubsub.unsubscribe("trades", "orderbook")
        await r.aclose()
