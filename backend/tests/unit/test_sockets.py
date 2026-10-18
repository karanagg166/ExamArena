"""Unit tests for WebSocket ConnectionManager, room partitioning, and event builders."""

from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocketDisconnect

from app.core.models import Role
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
from app.users.schemas import UserResponse


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


@pytest.mark.asyncio
async def test_websocket_authenticate_unauthenticated(mocker):
    """Unauthenticated connections (missing or invalid token) must be rejected."""
    from app.sockets.server import authenticate_websocket

    # No token at all
    ws_no_token = AsyncMock()
    ws_no_token.query_params = {}
    ws_no_token.cookies = {}
    ws_no_token.headers = {}
    user = await authenticate_websocket(ws_no_token)
    assert user is None

    # Invalid token
    mocker.patch("app.sockets.server.decode_token_claims", return_value=None)
    ws_invalid_token = AsyncMock()
    ws_invalid_token.query_params = {"token": "invalid_jwt"}
    ws_invalid_token.cookies = {}
    ws_invalid_token.headers = {}
    user = await authenticate_websocket(ws_invalid_token)
    assert user is None


@pytest.mark.asyncio
async def test_websocket_authenticate_revoked_token(mocker):
    """Blacklisted / revoked tokens must be rejected."""
    from app.sockets.server import authenticate_websocket

    mocker.patch(
        "app.sockets.server.decode_token_claims",
        return_value={"sub": "user-1", "jti": "revoked-jti"},
    )
    mocker.patch("app.sockets.server.is_token_blacklisted", return_value=True)

    ws = AsyncMock()
    ws.query_params = {"token": "revoked_token"}
    ws.cookies = {}
    ws.headers = {}
    user = await authenticate_websocket(ws)
    assert user is None


def _make_test_user(
    user_id: str = "usr-1",
    email: str = "test@example.com",
    name: str = "Test User",
    role: str = "STUDENT",
):
    from app.core.models import Role
    from app.users.schemas import UserResponse

    role_val = Role(role) if isinstance(role, str) else role
    return UserResponse(
        id=user_id,
        email=email,
        name=name,
        role=role_val,
        phoneNo="+919876543210",
        city="Mumbai",
        state="Maharashtra",
        country="India",
        pincode="400001",
        dateOfBirth="2000-01-01T00:00:00Z",
        createdAt="2026-01-01T00:00:00Z",
        updatedAt="2026-01-01T00:00:00Z",
    )


@pytest.mark.asyncio
async def test_websocket_authenticate_valid_token(mocker):
    """Valid token returns the authenticated user."""
    from app.core.models import Role
    from app.sockets.server import authenticate_websocket

    mock_user = _make_test_user("usr-123", "student@example.com", "Student A", Role.STUDENT)
    mocker.patch(
        "app.sockets.server.decode_token_claims",
        return_value={"sub": "usr-123", "jti": "valid-jti"},
    )
    mocker.patch("app.sockets.server.is_token_blacklisted", return_value=False)
    mocker.patch("app.sockets.server.get_user_by_id", return_value=mock_user)

    ws = AsyncMock()
    ws.query_params = {"token": "valid_token"}
    ws.cookies = {}
    ws.headers = {}
    user = await authenticate_websocket(ws)
    assert user is not None
    assert user.id == "usr-123"
    assert user.role == Role.STUDENT


@pytest.mark.asyncio
async def test_websocket_exam_authorization_cross_school(mocker):
    """Teacher or student from School B attempting to access exam from School A must be rejected."""
    from app.core.models import Role
    from app.sockets.server import authorize_exam_access

    # Teacher from School B
    teacher_user = _make_test_user("teacher-b", "teacherb@schoolb.com", "Teacher B", Role.TEACHER)
    mock_teacher_profile = mocker.MagicMock()
    mock_teacher_profile.id = "tch-b"
    mock_teacher_profile.schoolId = "school-B"

    # Exam belongs to School A
    mock_exam_creator = mocker.MagicMock()
    mock_exam_creator.id = "tch-a"
    mock_exam_creator.schoolId = "school-A"

    mock_exam = mocker.MagicMock()
    mock_exam.id = "exam-1"
    mock_exam.teacherId = "tch-a"
    mock_exam.teacher = mock_exam_creator
    mock_exam.isPublished = True

    mocker.patch("app.sockets.server.get_exam_by_id", return_value=mock_exam)
    mocker.patch("app.sockets.server.get_teacher_by_user_id", return_value=mock_teacher_profile)
    mocker.patch("app.sockets.server.can_manage_exam", return_value=False)

    authorized, _, _ = await authorize_exam_access(teacher_user, "exam-1")
    assert authorized is False

    # Student from School B attempting School A exam
    student_user = _make_test_user("student-b", "studentb@schoolb.com", "Student B", Role.STUDENT)
    mock_student_profile = mocker.MagicMock()
    mock_student_profile.id = "stu-b"
    mock_student_profile.schoolId = "school-B"

    mocker.patch("app.sockets.server.get_student_by_user_id", return_value=mock_student_profile)

    authorized, _, _ = await authorize_exam_access(student_user, "exam-1")
    assert authorized is False


@pytest.mark.asyncio
async def test_websocket_exam_authorization_valid_student_and_teacher(mocker):
    """Authorized student and creator teacher from same school must pass authorization."""
    from app.core.models import Role
    from app.sockets.server import authorize_exam_access

    mock_exam_creator = mocker.MagicMock()
    mock_exam_creator.id = "tch-a"
    mock_exam_creator.schoolId = "school-A"

    mock_exam = mocker.MagicMock()
    mock_exam.id = "exam-1"
    mock_exam.teacherId = "tch-a"
    mock_exam.teacher = mock_exam_creator
    mock_exam.isPublished = True

    mocker.patch("app.sockets.server.get_exam_by_id", return_value=mock_exam)

    # Creator teacher
    teacher_user = _make_test_user("usr-teacher-a", "teachera@schoola.com", "Teacher A", Role.TEACHER)
    mock_teacher_profile = mocker.MagicMock()
    mock_teacher_profile.id = "tch-a"
    mock_teacher_profile.schoolId = "school-A"
    mocker.patch("app.sockets.server.get_teacher_by_user_id", return_value=mock_teacher_profile)
    mocker.patch("app.sockets.server.can_manage_exam", return_value=True)

    authorized, exam_ret, prof = await authorize_exam_access(teacher_user, "exam-1")
    assert authorized is True
    assert exam_ret.id == "exam-1"

    # Enrolled student from School A
    student_user = _make_test_user("usr-student-a", "studenta@schoola.com", "Student A", Role.STUDENT)
    mock_student_profile = mocker.MagicMock()
    mock_student_profile.id = "stu-a"
    mock_student_profile.schoolId = "school-A"
    mocker.patch("app.sockets.server.get_student_by_user_id", return_value=mock_student_profile)

    authorized, exam_ret, prof = await authorize_exam_access(student_user, "exam-1")
    assert authorized is True
    assert prof.id == "stu-a"


@pytest.mark.asyncio
async def test_websocket_exam_endpoint_lifecycle_and_security(mocker):
    """Test full WebSocket endpoint lifecycle: reject unauth, prevent spoofing & forged events."""
    from fastapi import WebSocketDisconnect

    from app.core.models import Role
    from app.sockets.server import exam_websocket_endpoint

    # 1. Unauthenticated client rejected with WS_1008
    mocker.patch("app.sockets.server.authenticate_websocket", return_value=None)
    ws_unauth = AsyncMock()
    await exam_websocket_endpoint(ws_unauth, "exam-1")
    ws_unauth.close.assert_awaited_once_with(code=1008, reason="Unauthorized")

    # 2. Student connects and attempts identity spoofing + forged privileged events
    student_user = _make_test_user("student-real-id", "student@schoola.com", "Student Real", Role.STUDENT)
    mocker.patch("app.sockets.server.authenticate_websocket", return_value=student_user)

    mock_student_profile = mocker.MagicMock()
    mock_student_profile.id = "stu-prof-real"
    mock_student_profile.schoolId = "school-A"

    mock_exam = mocker.MagicMock()
    mock_exam.id = "exam-1"
    mocker.patch(
        "app.sockets.server.authorize_exam_access",
        return_value=(True, mock_exam, mock_student_profile),
    )

    # Client sends:
    # 1. exam:join with spoofed userId: "admin"
    # 2. exam:time_sync (privileged event forbidden for students)
    # 3. proctoring:terminate (privileged event forbidden for students)
    # 4. proctoring:warning with spoofed studentId: "other-student"
    # 5. Disconnect
    ws_client = AsyncMock()
    ws_client.receive_json.side_effect = [
        {"event": "exam:join", "data": {"userId": "spoofed-admin", "role": "ADMIN"}},
        {"event": "exam:time_sync", "data": {"remainingSeconds": 0}},
        {"event": "proctoring:terminate", "data": {"studentId": "victim-student"}},
        {"event": "proctoring:warning", "data": {"studentId": "victim-student", "warningCount": 3}},
        WebSocketDisconnect(),
    ]

    mock_broadcast = mocker.patch("app.sockets.manager.manager.broadcast", new_callable=AsyncMock)
    mock_send_personal = mocker.patch(
        "app.sockets.manager.manager.send_personal_message", new_callable=AsyncMock
    )
    mocker.patch("app.sockets.manager.manager.connect", new_callable=AsyncMock)
    mocker.patch("app.sockets.manager.manager.disconnect")

    await exam_websocket_endpoint(ws_client, "exam-1")

    # Verify exam:join broadcast used the REAL authenticated student_user identity, NOT spoofed-admin!
    join_call = mock_broadcast.call_args_list[0]
    join_event = join_call[0][1]
    assert join_event["event"] == "exam:join"
    assert join_event["data"]["userId"] == "student-real-id"
    assert join_event["data"]["role"] == Role.STUDENT

    # Verify time_sync was NOT broadcast, but sent an error to client
    broadcast_events = [c[0][1]["event"] for c in mock_broadcast.call_args_list]
    assert "exam:time_sync" not in broadcast_events
    assert "proctoring:terminate" not in broadcast_events

    # Verify personal error messages were sent back to the student
    personal_messages = [c[0][0] for c in mock_send_personal.call_args_list]
    assert any("Unauthorized to synchronize timer" in str(msg) for msg in personal_messages)
    assert any("Unauthorized to terminate exam" in str(msg) for msg in personal_messages)

    # Verify proctoring:warning was sanitized to student's own ID
    warning_event = [c[0][1] for c in mock_broadcast.call_args_list if c[0][1]["event"] == "proctoring:warning"][0]
    assert warning_event["data"]["studentId"] == "stu-prof-real"


@pytest.mark.asyncio
async def test_authorize_exam_access_strict_school_isolation(mocker):
    """Students cannot join WebSocket rooms for exams belonging to a different school or unpublished exams."""
    from app.sockets.server import authorize_exam_access

    mock_student_user = mocker.MagicMock(spec=UserResponse)
    mock_student_user.id = "student-1"
    mock_student_user.role = Role.STUDENT

    mock_student_profile = mocker.MagicMock()
    mock_student_profile.id = "stu-prof-1"
    mock_student_profile.schoolId = "school-A"
    mock_student_profile.classId = "class-1"
    mocker.patch("app.sockets.server.get_student_by_user_id", return_value=mock_student_profile)

    # Exam from school-B
    mock_exam_diff_school = mocker.MagicMock()
    mock_exam_diff_school.isPublished = True
    mock_exam_diff_school.teacher = mocker.MagicMock(schoolId="school-B")
    mocker.patch("app.sockets.server.get_exam_by_id", return_value=mock_exam_diff_school)

    allowed, _, _ = await authorize_exam_access(mock_student_user, "exam-1")
    assert allowed is False

    # Exam from same school, but unpublished
    mock_exam_unpublished = mocker.MagicMock()
    mock_exam_unpublished.isPublished = False
    mock_exam_unpublished.teacher = mocker.MagicMock(schoolId="school-A")
    mocker.patch("app.sockets.server.get_exam_by_id", return_value=mock_exam_unpublished)

    allowed, _, _ = await authorize_exam_access(mock_student_user, "exam-2")
    assert allowed is False

    # Exam from same school and published
    mock_exam_valid = mocker.MagicMock()
    mock_exam_valid.isPublished = True
    mock_exam_valid.teacher = mocker.MagicMock(schoolId="school-A")
    mocker.patch("app.sockets.server.get_exam_by_id", return_value=mock_exam_valid)

    allowed, _, _ = await authorize_exam_access(mock_student_user, "exam-3")
    assert allowed is True


@pytest.mark.asyncio
async def test_general_websocket_endpoint_school_room_scoping(mocker):
    """Verify general /ws presence room is partitioned by schoolId for multi-tenant isolation."""
    from app.sockets.server import general_websocket_endpoint

    mock_student_user = mocker.MagicMock(spec=UserResponse)
    mock_student_user.id = "stu-u1"
    mock_student_user.role = Role.STUDENT

    mock_student_profile = mocker.MagicMock()
    mock_student_profile.schoolId = "school-xyz"
    mocker.patch("app.sockets.server.authenticate_websocket", return_value=mock_student_user)
    mocker.patch("app.sockets.server.get_student_by_user_id", return_value=mock_student_profile)

    mock_connect = mocker.patch("app.sockets.manager.manager.connect", new_callable=AsyncMock)
    mocker.patch("app.sockets.manager.manager.disconnect")

    ws = AsyncMock()
    ws.receive_json.side_effect = WebSocketDisconnect()

    await general_websocket_endpoint(ws)
    mock_connect.assert_awaited_once_with(ws, "school_school-xyz")

