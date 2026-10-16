"""Chat socket event constructors."""

from datetime import UTC, datetime, timezone
from typing import Any


def create_chat_message_event(
    sender_id: str, sender_name: str, room: str, text: str
) -> dict[str, Any]:
    """Constructs a real-time chat message broadcast payload."""
    return {
        "event": "chat:message",
        "data": {
            "senderId": sender_id,
            "senderName": sender_name,
            "room": room,
            "text": text,
            "sentAt": datetime.now(UTC).isoformat(),
        },
    }
