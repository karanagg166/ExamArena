"""Connection manager for FastAPI WebSockets with room partitioning."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSockets categorized by room."""

    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str) -> None:
        """Accepts a websocket connection and binds it to a room."""
        await websocket.accept()
        if room not in self._rooms:
            self._rooms[room] = set()
        self._rooms[room].add(websocket)
        logger.info(
            "WebSocket connected to room %s (total: %d)", room, len(self._rooms[room])
        )

    def disconnect(self, websocket: WebSocket, room: str) -> None:
        """Removes a websocket from a room."""
        if room in self._rooms and websocket in self._rooms[room]:
            self._rooms[room].remove(websocket)
            if not self._rooms[room]:
                del self._rooms[room]
            logger.info("WebSocket disconnected from room %s", room)

    async def send_personal_message(
        self, message: dict[str, Any], websocket: WebSocket
    ) -> None:
        """Sends a JSON message directly to a single connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning("Failed to send personal websocket message: %s", e)

    async def broadcast(
        self,
        room: str,
        message: dict[str, Any],
        exclude: WebSocket | None = None,
    ) -> None:
        """Broadcasts a JSON message to all connections in a room."""
        connections = self._rooms.get(room, set()).copy()
        for connection in connections:
            if connection != exclude:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(
                        "Failed to broadcast message in room %s: %s", room, e
                    )
                    self.disconnect(connection, room)

    def get_room_occupancy(self, room: str) -> int:
        """Returns the number of active clients in a room."""
        return len(self._rooms.get(room, set()))


manager = ConnectionManager()
