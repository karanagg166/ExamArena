"""Sockets package initialization."""

from app.sockets.manager import ConnectionManager, manager
from app.sockets.namespaces import exam_room, school_room, user_room
from app.sockets.server import router as socket_router

__all__ = [
    "ConnectionManager",
    "manager",
    "exam_room",
    "school_room",
    "user_room",
    "socket_router",
]
