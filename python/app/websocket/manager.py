import asyncio
from typing import List

import redis.asyncio as redis
from app.core.config import settings
from app.core.logger import get_logger
from fastapi import WebSocket

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            f"[WS] Client connected | total={len(self.active_connections)} client={websocket.client}"
        )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                f"[WS] Client disconnected | total={len(self.active_connections)} client={websocket.client}"
            )

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
        logger.debug(f"[WS] Personal message sent | len={len(message)}")

    async def broadcast(self, message: str):
        if not self.active_connections:
            return  # Nothing to broadcast — skip quietly

        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(
                    f"[WS] Failed to send to client | client={connection.client} error={e}"
                )
                dead.append(connection)

        # Clean up dead connections
        for conn in dead:
            if conn in self.active_connections:
                self.active_connections.remove(conn)
                logger.info(
                    f"[WS] Removed dead connection | remaining={len(self.active_connections)}"
                )

        if self.active_connections:
            logger.debug(
                f"[WS] Broadcast complete | clients={len(self.active_connections)} payload_len={len(message)}"
            )


manager = ConnectionManager()


async def redis_pubsub_listener(connection_manager: ConnectionManager):
    """
    Subscribes to Redis pub/sub channels and broadcasts messages to all
    connected WebSockets. Uses polling with get_message() to avoid socket
    timeout errors. Auto-reconnects on transient Redis errors.
    """
    CHANNELS = ["trade", "orderbook", "price", "user_update"]
    RETRY_DELAY = 5  # seconds before reconnect attempt
    reconnect_count = 0
    total_messages = 0

    logger.info(f"[PubSub] Redis listener starting | channels={CHANNELS}")

    while True:
        r = None
        pubsub = None
        try:
            logger.debug(
                f"[PubSub] Connecting to Redis | url={settings.REDIS_URL} attempt={reconnect_count + 1}"
            )
            r = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            await r.ping()  # verify connection before subscribing
            pubsub = r.pubsub()
            await pubsub.subscribe(*CHANNELS)
            reconnect_count += 1
            logger.info(
                f"[PubSub] Subscribed to Redis channels | channels={CHANNELS} reconnect_count={reconnect_count}"
            )

            # Poll for messages — avoids blocking listen() socket timeout errors
            while True:
                try:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True, timeout=1.0
                    )
                    if message and message.get("type") == "message":
                        data = message.get("data")
                        channel = message.get("channel", "?")
                        if data:
                            total_messages += 1
                            logger.debug(
                                f"[PubSub] Message received | channel={channel} len={len(data)} total={total_messages}"
                            )
                            try:
                                await connection_manager.broadcast(data)
                            except Exception as e:
                                logger.warning(
                                    f"[PubSub] Broadcast error | channel={channel} error={e}"
                                )
                    else:
                        # No message this tick — yield control briefly
                        await asyncio.sleep(0.05)

                except asyncio.CancelledError:
                    raise  # Propagate to outer try for clean shutdown
                except Exception as e:
                    logger.error(
                        f"[PubSub] get_message error | error={e}", exc_info=True
                    )
                    break  # Break inner loop to trigger reconnect

        except asyncio.CancelledError:
            logger.info(
                f"[PubSub] Listener cancelled — shutting down cleanly | messages_processed={total_messages}"
            )
            break  # Exit the outer while loop

        except Exception as e:
            logger.error(
                f"[PubSub] Connection error | error={e} retrying_in={RETRY_DELAY}s",
                exc_info=True,
            )
            await asyncio.sleep(RETRY_DELAY)

        finally:
            # Always clean up, even if variables were never assigned
            try:
                if pubsub is not None:
                    await pubsub.unsubscribe(*CHANNELS)
                    await pubsub.aclose()
                    logger.debug("[PubSub] Pubsub connection closed")
            except Exception:
                pass
            try:
                if r is not None:
                    await r.aclose()
                    logger.debug("[PubSub] Redis connection closed")
            except Exception:
                pass
