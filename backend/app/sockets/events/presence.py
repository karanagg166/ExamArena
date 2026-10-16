"""Presence socket event constructors."""

from datetime import UTC, datetime, timezone
from typing import Any


def create_presence_join_event(user_id: str, role: str, room: str) -> dict[str, Any]:
    """Constructs a presence join event payload."""
    return {
        "event": "presence:user_joined",
        "data": {
            "userId": user_id,
            "role": role,
            "room": room,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    }


def create_presence_leave_event(user_id: str, room: str) -> dict[str, Any]:
    """Constructs a presence leave event payload."""
    return {
        "event": "presence:user_left",
        "data": {
            "userId": user_id,
            "room": room,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    }
