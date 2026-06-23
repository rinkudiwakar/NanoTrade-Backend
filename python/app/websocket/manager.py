import asyncio
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
    Subscribes to Redis pub/sub channels and broadcasts messages to all
    connected WebSockets. Uses polling with get_message() to avoid socket
    timeout errors. Auto-reconnects on transient Redis errors.
    """
    CHANNELS = ["trade", "orderbook", "price", "user_update"]
    RETRY_DELAY = 5  # seconds before reconnect attempt

    while True:
        r = None
        pubsub = None
        try:
            r = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            await r.ping()  # verify connection before subscribing
            pubsub = r.pubsub()
            await pubsub.subscribe(*CHANNELS)
            print(f"Redis pubsub listener: subscribed to {CHANNELS}")

            # Poll for messages — avoids blocking listen() socket timeout errors
            while True:
                try:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0
                    )
                    if message and message.get("type") == "message":
                        data = message.get("data")
                        if data:
                            try:
                                await connection_manager.broadcast(data)
                            except Exception as e:
                                print(f"Failed to broadcast WebSocket message: {e}")
                    else:
                        # No message this tick — yield control briefly
                        await asyncio.sleep(0.05)

                except asyncio.CancelledError:
                    raise  # Propagate to outer try for clean shutdown
                except Exception as e:
                    print(f"Redis get_message error: {e}")
                    break  # Break inner loop to trigger reconnect

        except asyncio.CancelledError:
            print("Redis pubsub listener: shutting down cleanly.")
            break  # Exit the outer while loop

        except Exception as e:
            print(f"Redis pubsub listener: connection error — {e}. Retrying in {RETRY_DELAY}s...")
            await asyncio.sleep(RETRY_DELAY)

        finally:
            # Always clean up, even if variables were never assigned
            try:
                if pubsub is not None:
                    await pubsub.unsubscribe(*CHANNELS)
                    await pubsub.aclose()
            except Exception:
                pass
            try:
                if r is not None:
                    await r.aclose()
            except Exception:
                pass
