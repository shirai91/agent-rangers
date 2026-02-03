"""WebSocket API for real-time board updates."""

import asyncio
import json
from typing import Dict, Set
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from redis.asyncio import Redis
import redis.asyncio as redis_async

from app.config import settings

router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections per board.

    Handles broadcasting updates to all clients connected to a specific board
    using Redis pub/sub for multi-instance support.
    """

    def __init__(self):
        """Initialize connection manager with empty connection pools."""
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.redis_client: Redis | None = None
        self.pubsub = None
        self.listener_task = None

    async def initialize_redis(self):
        """Initialize Redis connection and pub/sub."""
        if self.redis_client is None:
            self.redis_client = redis_async.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            self.pubsub = self.redis_client.pubsub()
            # Subscribe to all board channels
            await self.pubsub.psubscribe("board:*")
            # Start listener task
            self.listener_task = asyncio.create_task(self._redis_listener())

    async def close_redis(self):
        """Close Redis connection."""
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()

    async def _redis_listener(self):
        """Listen for Redis pub/sub messages and broadcast to WebSocket clients."""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "pmessage":
                    # Extract board_id from channel name (format: board:{board_id})
                    channel = message["channel"]
                    board_id = channel.split(":")[1]
                    data = message["data"]

                    # Broadcast to all WebSocket connections for this board
                    if board_id in self.active_connections:
                        await self._broadcast_to_board(board_id, data)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Redis listener error: {e}")

    async def connect(self, websocket: WebSocket, board_id: str):
        """
        Connect a WebSocket client to a board.

        Args:
            websocket: WebSocket connection
            board_id: Board UUID as string
        """
        await websocket.accept()
        if board_id not in self.active_connections:
            self.active_connections[board_id] = set()
        self.active_connections[board_id].add(websocket)

    def disconnect(self, websocket: WebSocket, board_id: str):
        """
        Disconnect a WebSocket client from a board.

        Args:
            websocket: WebSocket connection
            board_id: Board UUID as string
        """
        if board_id in self.active_connections:
            self.active_connections[board_id].discard(websocket)
            if not self.active_connections[board_id]:
                del self.active_connections[board_id]

    async def _broadcast_to_board(self, board_id: str, message: str):
        """
        Broadcast a message to all clients connected to a board.

        Args:
            board_id: Board UUID as string
            message: JSON message to broadcast
        """
        if board_id not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[board_id]:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, board_id)

    async def broadcast(self, board_id: str, message: dict):
        """
        Broadcast a message to all instances via Redis pub/sub.

        Args:
            board_id: Board UUID as string
            message: Message dictionary to broadcast
        """
        if self.redis_client:
            channel = f"board:{board_id}"
            await self.redis_client.publish(channel, json.dumps(message))

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """
        Send a message to a specific WebSocket client.

        Args:
            message: Message to send
            websocket: Target WebSocket connection
        """
        await websocket.send_text(message)


# Global connection manager instance
manager = ConnectionManager()


async def get_manager() -> ConnectionManager:
    """
    Dependency for getting the connection manager.

    Ensures Redis is initialized.

    Returns:
        ConnectionManager instance
    """
    if manager.redis_client is None:
        await manager.initialize_redis()
    return manager


@router.on_event("startup")
async def startup_event():
    """Initialize Redis connection on startup."""
    await manager.initialize_redis()


@router.on_event("shutdown")
async def shutdown_event():
    """Close Redis connection on shutdown."""
    await manager.close_redis()


@router.websocket("/boards/{board_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    board_id: UUID,
    conn_manager: ConnectionManager = Depends(get_manager),
):
    """
    WebSocket endpoint for real-time board updates.

    Clients connect to receive real-time updates about task and column changes.

    Message format (from server to client):
    ```json
    {
        "type": "task_created" | "task_updated" | "task_moved" | "task_deleted" |
                "column_created" | "column_updated" | "column_deleted",
        "payload": {
            "task_id": "uuid",
            "column_id": "uuid",
            "data": {...}
        }
    }
    ```

    Args:
        websocket: WebSocket connection
        board_id: Board UUID
        conn_manager: Connection manager dependency
    """
    board_id_str = str(board_id)
    await conn_manager.connect(websocket, board_id_str)

    try:
        # Send initial connection confirmation
        await conn_manager.send_personal_message(
            json.dumps({
                "type": "connected",
                "payload": {"board_id": board_id_str}
            }),
            websocket,
        )

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Handle ping/pong for connection health
            if data == "ping":
                await websocket.send_text("pong")
            else:
                # Echo back for debugging (remove in production)
                await conn_manager.send_personal_message(
                    json.dumps({
                        "type": "echo",
                        "payload": json.loads(data)
                    }),
                    websocket,
                )

    except WebSocketDisconnect:
        conn_manager.disconnect(websocket, board_id_str)
    except Exception as e:
        print(f"WebSocket error: {e}")
        conn_manager.disconnect(websocket, board_id_str)


async def notify_board_update(board_id: UUID, event_type: str, payload: dict):
    """
    Helper function to notify all clients about a board update.

    Should be called from API endpoints after database changes.

    Args:
        board_id: Board UUID
        event_type: Type of event (task_created, task_updated, etc.)
        payload: Event payload data
    """
    if manager.redis_client:
        await manager.broadcast(
            str(board_id),
            {
                "type": event_type,
                "payload": payload,
            }
        )
