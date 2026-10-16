"""Unit tests for WebSocket ConnectionManager, room partitioning, and event builders."""

from unittest.mock import AsyncMock

import pytest

from app.sockets.events.chat import create_chat_message_event
from app.sockets.events.exam import (
    create_exam_join_event,
    create_exam_submit_event,
    create_exam_time_sync_event,
)
from app.sockets.events.presence import (
    create_presence_join_event,
    create_presence_leave_event,
)
from app.sockets.events.proctoring import (
    create_proctoring_termination_event,
    create_proctoring_warning_event,
)
from app.sockets.manager import ConnectionManager
from app.sockets.namespaces import (
    chat_room,
    exam_room,
    proctoring_room,
    school_room,
    user_room,
)


def test_namespace_helpers():
    assert exam_room("exam-123") == "exam:exam-123"
    assert proctoring_room("exam-123") == "proctoring:exam-123"
    assert chat_room("exam-123") == "chat:exam-123"
    assert user_room("user-123") == "user:user-123"
    assert school_room("school-123") == "school:school-123"


def test_exam_event_builders():
    join_ev = create_exam_join_event("exam-123", "user-1", "student")
    assert join_ev["event"] == "exam:join"
    assert join_ev["data"]["examId"] == "exam-123"
    assert join_ev["data"]["userId"] == "user-1"
    assert join_ev["data"]["role"] == "student"
    assert "joinedAt" in join_ev["data"]

    submit_ev = create_exam_submit_event("exam-123", "student-1", "attempt-1")
    assert submit_ev["event"] == "exam:submit"
    assert submit_ev["data"]["examId"] == "exam-123"
    assert submit_ev["data"]["studentId"] == "student-1"
    assert submit_ev["data"]["attemptId"] == "attempt-1"
    assert "submittedAt" in submit_ev["data"]

    sync_ev = create_exam_time_sync_event("exam-123", 3600)
    assert sync_ev["event"] == "exam:time_sync"
    assert sync_ev["data"]["examId"] == "exam-123"
    assert sync_ev["data"]["remainingSeconds"] == 3600
    assert "syncedAt" in sync_ev["data"]


def test_presence_event_builders():
    join_ev = create_presence_join_event("user-1", "student", "room-1")
    assert join_ev["event"] == "presence:user_joined"
    assert join_ev["data"]["userId"] == "user-1"
    assert join_ev["data"]["role"] == "student"
    assert join_ev["data"]["room"] == "room-1"
    assert "timestamp" in join_ev["data"]

    leave_ev = create_presence_leave_event("user-1", "room-1")
    assert leave_ev["event"] == "presence:user_left"
    assert leave_ev["data"]["userId"] == "user-1"
    assert leave_ev["data"]["room"] == "room-1"
    assert "timestamp" in leave_ev["data"]


def test_proctoring_event_builders():
    warn_ev = create_proctoring_warning_event(
        "exam-123", "student-1", 2, "Tab switched"
    )
    assert warn_ev["event"] == "proctoring:warning"
    assert warn_ev["data"]["examId"] == "exam-123"
    assert warn_ev["data"]["studentId"] == "student-1"
    assert warn_ev["data"]["warningCount"] == 2
    assert warn_ev["data"]["reason"] == "Tab switched"
    assert "timestamp" in warn_ev["data"]

    term_ev = create_proctoring_termination_event(
        "exam-123", "student-1", "Max violations reached"
    )
    assert term_ev["event"] == "proctoring:terminate"
    assert term_ev["data"]["examId"] == "exam-123"
    assert term_ev["data"]["studentId"] == "student-1"
    assert term_ev["data"]["reason"] == "Max violations reached"
    assert "terminatedAt" in term_ev["data"]


def test_chat_event_builders():
    msg_ev = create_chat_message_event("user-1", "Alice", "room-1", "Hello class")
    assert msg_ev["event"] == "chat:message"
    assert msg_ev["data"]["senderId"] == "user-1"
    assert msg_ev["data"]["senderName"] == "Alice"
    assert msg_ev["data"]["room"] == "room-1"
    assert msg_ev["data"]["text"] == "Hello class"
    assert "sentAt" in msg_ev["data"]


@pytest.mark.asyncio
async def test_connection_manager_room_partitioning():
    cm = ConnectionManager()

    ws1 = AsyncMock()
    ws2 = AsyncMock()
    ws3 = AsyncMock()

    await cm.connect(ws1, "room-A")
    await cm.connect(ws2, "room-A")
    await cm.connect(ws3, "room-B")

    assert cm.get_room_occupancy("room-A") == 2
    assert cm.get_room_occupancy("room-B") == 1
    assert cm.get_room_occupancy("room-C") == 0

    # Broadcast to room-A only
    message = {"type": "TEST", "payload": {}}
    await cm.broadcast("room-A", message)

    ws1.send_json.assert_awaited_once_with(message)
    ws2.send_json.assert_awaited_once_with(message)
    ws3.send_json.assert_not_awaited()

    # Disconnect ws1
    cm.disconnect(ws1, "room-A")
    assert cm.get_room_occupancy("room-A") == 1

    # Disconnect ws2
    cm.disconnect(ws2, "room-A")
    assert cm.get_room_occupancy("room-A") == 0


@pytest.mark.asyncio
async def test_connection_manager_dead_socket_cleanup():
    cm = ConnectionManager()

    bad_ws = AsyncMock()
    bad_ws.send_json.side_effect = RuntimeError("Broken pipe")

    await cm.connect(bad_ws, "room-A")
    assert cm.get_room_occupancy("room-A") == 1

    # Broadcast should catch the error and remove the dead socket
    await cm.broadcast("room-A", {"type": "PING"})
    assert cm.get_room_occupancy("room-A") == 0
