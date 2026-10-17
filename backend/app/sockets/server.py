"""FastAPI WebSocket server endpoints and event dispatchers with strict authentication and RBAC."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.auth.token_blacklist import is_token_blacklisted
from app.core.models import Role
from app.core.security import decode_token_claims
from app.exams.crud import get_exam_by_id
from app.exams.permissions import can_manage_exam
from app.sockets.events.exam import (
    create_exam_join_event,
    create_exam_submit_event,
    create_exam_time_sync_event,
)
from app.sockets.events.presence import (
    create_presence_join_event,
)
from app.sockets.events.proctoring import (
    create_proctoring_termination_event,
    create_proctoring_warning_event,
)
from app.sockets.manager import manager
from app.sockets.namespaces import exam_room
from app.students.crud import get_student_by_user_id
from app.teachers.crud import get_teacher_by_user_id
from app.users.crud import get_user_by_id
from app.users.schemas import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sockets"])


async def authenticate_websocket(websocket: WebSocket) -> UserResponse | None:
    """Extract and verify JWT credentials from WebSocket query params, cookies, or headers."""
    token = websocket.query_params.get("token") or websocket.cookies.get("access_token")
    if not token:
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()

    if not token:
        return None

    claims = decode_token_claims(token)
    if not claims:
        return None

    jti = claims.get("jti")
    if jti:
        try:
            if await is_token_blacklisted(jti):
                return None
        except Exception:
            return None

    user_id = claims.get("sub")
    if not user_id:
        return None

    user = await get_user_by_id(str(user_id))
    return user


async def authorize_exam_access(
    user: UserResponse, exam_id: str
) -> tuple[bool, Any | None, Any | None]:
    """Verify that an authenticated user has legitimate access to an exam room."""
    exam = await get_exam_by_id(exam_id)
    if not exam:
        return False, None, None

    if user.role == Role.ADMIN:
        return True, exam, None

    if user.role in (Role.TEACHER, Role.PRINCIPAL):
        teacher = await get_teacher_by_user_id(user.id)
        if not teacher:
            return False, exam, None
        # Enforce cross-school isolation
        if (
            exam.teacher
            and exam.teacher.schoolId
            and teacher.schoolId
            and exam.teacher.schoolId != teacher.schoolId
        ):
            return False, exam, teacher
        if not can_manage_exam(user, teacher, exam):
            return False, exam, teacher
        return True, exam, teacher

    if user.role == Role.STUDENT:
        student = await get_student_by_user_id(user.id)
        if not student:
            return False, exam, None
        # Enforce cross-school isolation
        if (
            exam.teacher
            and exam.teacher.schoolId
            and student.schoolId
            and exam.teacher.schoolId != student.schoolId
        ):
            return False, exam, student
        if not exam.isPublished:
            return False, exam, student
        return True, exam, student

    return False, exam, None


@router.websocket("/ws")
async def general_websocket_endpoint(websocket: WebSocket):
    """General WebSocket connection for notifications and presence with mandatory authentication."""
    user = await authenticate_websocket(websocket)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
        return

    room = "general"
    await manager.connect(websocket, room)
    try:
        while True:
            data: dict[str, Any] = await websocket.receive_json()
            event = data.get("event")

            if event == "heartbeat":
                await manager.send_personal_message(
                    {"event": "heartbeat:ack", "status": "ok"}, websocket
                )
            elif event == "presence:join":
                # User identity and role derived strictly from authenticated session
                user_id = user.id
                role = user.role
                evt = create_presence_join_event(user_id, role, room)
                await manager.broadcast(room, evt, exclude=websocket)
            else:
                logger.debug(
                    "Ignored unprivileged or unknown event on /ws: %s from user %s",
                    event,
                    user.id,
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
    except Exception as e:
        logger.warning("Error in general websocket loop: %s", e)
        manager.disconnect(websocket, room)


@router.websocket("/ws/exam/{exam_id}")
async def exam_websocket_endpoint(websocket: WebSocket, exam_id: str):
    """Realtime exam room with strict authentication, RBAC, and tenant boundaries."""
    user = await authenticate_websocket(websocket)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
        return

    is_authorized, exam, profile = await authorize_exam_access(user, exam_id)
    if not is_authorized:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Forbidden: Access denied to this exam room",
        )
        return

    room = exam_room(exam_id)
    await manager.connect(websocket, room)
    try:
        while True:
            data: dict[str, Any] = await websocket.receive_json()
            event = data.get("event")
            payload = data.get("data", {})

            if event == "heartbeat":
                await manager.send_personal_message(
                    {"event": "heartbeat:ack", "examId": exam_id}, websocket
                )

            elif event == "exam:join":
                # Derive identity strictly from authenticated session
                evt = create_exam_join_event(exam_id, user.id, user.role)
                await manager.broadcast(room, evt, exclude=websocket)

            elif event == "exam:submit":
                student_id = profile.id if profile and user.role == Role.STUDENT else user.id
                attempt_id = str(payload.get("attemptId", ""))
                evt = create_exam_submit_event(exam_id, student_id, attempt_id)
                await manager.broadcast(room, evt, exclude=websocket)

            elif event == "exam:time_sync":
                # Only teachers, principals, or admins managing this exam can synchronize time
                if user.role not in (Role.TEACHER, Role.PRINCIPAL, Role.ADMIN):
                    logger.warning(
                        "Student %s attempted unauthorized timer sync in exam %s",
                        user.id,
                        exam_id,
                    )
                    await manager.send_personal_message(
                        {"error": "Unauthorized to synchronize timer", "event": "error"},
                        websocket,
                    )
                    continue

                rem_seconds = int(payload.get("remainingSeconds", 0))
                evt = create_exam_time_sync_event(exam_id, rem_seconds)
                await manager.broadcast(room, evt, exclude=websocket)

            elif event == "proctoring:warning":
                # Students may only log warnings for their own attempt
                if user.role == Role.STUDENT:
                    student_id = profile.id if profile else user.id
                else:
                    student_id = str(payload.get("studentId", ""))

                count = int(payload.get("warningCount", 1))
                reason = str(payload.get("reason", "Violation detected"))
                evt = create_proctoring_warning_event(
                    exam_id, student_id, count, reason
                )
                await manager.broadcast(room, evt, exclude=websocket)

            elif event == "proctoring:terminate":
                # Privileged action: students cannot trigger exam termination
                if user.role not in (Role.TEACHER, Role.PRINCIPAL, Role.ADMIN):
                    logger.warning(
                        "Student %s attempted unauthorized proctoring termination in exam %s",
                        user.id,
                        exam_id,
                    )
                    await manager.send_personal_message(
                        {"error": "Unauthorized to terminate exam", "event": "error"},
                        websocket,
                    )
                    continue

                student_id = str(payload.get("studentId", ""))
                reason = str(payload.get("reason", "Maximum violations exceeded"))
                evt = create_proctoring_termination_event(exam_id, student_id, reason)
                await manager.broadcast(room, evt)

            else:
                # Do not blindly broadcast unvalidated or unknown payloads
                logger.debug(
                    "Refusing to broadcast unvalidated event '%s' from user %s in exam %s",
                    event,
                    user.id,
                    exam_id,
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
    except Exception as e:
        logger.warning("Error in exam websocket loop (%s): %s", exam_id, e)
        manager.disconnect(websocket, room)
