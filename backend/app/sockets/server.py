"""FastAPI WebSocket server endpoints and event dispatchers."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

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
from app.sockets.manager import manager
from app.sockets.namespaces import exam_room

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sockets"])


@router.websocket("/ws")
async def general_websocket_endpoint(websocket: WebSocket):
    """General WebSocket connection for notifications and presence."""
    room = "general"
    await manager.connect(websocket, room)
    try:
        while True:
            data: dict[str, Any] = await websocket.receive_json()
            event = data.get("event")
            payload = data.get("data", {})

            if event == "heartbeat":
                await manager.send_personal_message(
                    {"event": "heartbeat:ack", "status": "ok"}, websocket
                )
            elif event == "presence:join":
                user_id = str(payload.get("userId", "anonymous"))
                role = str(payload.get("role", "guest"))
                evt = create_presence_join_event(user_id, role, room)
                await manager.broadcast(room, evt, exclude=websocket)
            else:
                # Forward generic messages within the general room
                await manager.broadcast(room, data, exclude=websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
    except Exception as e:
        logger.warning("Error in general websocket loop: %s", e)
        manager.disconnect(websocket, room)


@router.websocket("/ws/exam/{exam_id}")
async def exam_websocket_endpoint(websocket: WebSocket, exam_id: str):
    """Realtime exam room for student synchronization, timer updates, and proctoring events."""
    room = exam_room(exam_id)
    await manager.connect(websocket, room)
    try:
        while True:
            data: dict[str, Any] = await websocket.receive_json()
            event = data.get("event")
            payload = data.get("data", {})

            if event == "exam:join":
                user_id = str(payload.get("userId", "student"))
                role = str(payload.get("role", "STUDENT"))
                evt = create_exam_join_event(exam_id, user_id, role)
                await manager.broadcast(room, evt, exclude=websocket)

            elif event == "exam:submit":
                student_id = str(payload.get("studentId", ""))
                attempt_id = str(payload.get("attemptId", ""))
                evt = create_exam_submit_event(exam_id, student_id, attempt_id)
                await manager.broadcast(room, evt, exclude=websocket)

            elif event == "exam:time_sync":
                rem_seconds = int(payload.get("remainingSeconds", 0))
                evt = create_exam_time_sync_event(exam_id, rem_seconds)
                await manager.broadcast(room, evt, exclude=websocket)

            elif event == "proctoring:warning":
                student_id = str(payload.get("studentId", ""))
                count = int(payload.get("warningCount", 1))
                reason = str(payload.get("reason", "Violation detected"))
                evt = create_proctoring_warning_event(
                    exam_id, student_id, count, reason
                )
                await manager.broadcast(room, evt, exclude=websocket)

            elif event == "proctoring:terminate":
                student_id = str(payload.get("studentId", ""))
                reason = str(payload.get("reason", "Maximum violations exceeded"))
                evt = create_proctoring_termination_event(exam_id, student_id, reason)
                await manager.broadcast(room, evt)

            elif event == "heartbeat":
                await manager.send_personal_message(
                    {"event": "heartbeat:ack", "examId": exam_id}, websocket
                )
            else:
                await manager.broadcast(room, data, exclude=websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
    except Exception as e:
        logger.warning("Error in exam websocket loop (%s): %s", exam_id, e)
        manager.disconnect(websocket, room)
