from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.models import (
    ClassJoinRequest,
    JoinRequestStatus,
    Notification,
    SchoolClass,
    Student,
)
from app.join_requests.crud import decide_join_request
from app.join_requests.schemas import JoinRequestResponse
from tests.dummy_data.schools import make_fake_school_class
from tests.dummy_data.students import make_fake_student
from tests.dummy_data.teachers import make_fake_teacher


def make_request(**overrides):
    data = {
        "id": "request_001",
        "studentUserId": "clxfake000000testuser",
        "classId": "clxfake_class_001",
        "className": "12th - A",
        "status": "PENDING",
        "requestedAt": datetime.now(UTC),
        "decidedAt": None,
        "studentName": "Test User",
        "studentEmail": "testuser@examarena.dev",
    }
    data.update(overrides)
    return JoinRequestResponse(**data)


@pytest.mark.asyncio
class TestJoinRequestsApi:
    async def test_join_by_invalid_code(
        self, client, override_auth, mock_join_request_db
    ):
        override_auth(role="STUDENT")
        mock_join_request_db["get_student_by_user_id"].return_value = None
        mock_join_request_db["get_class_by_join_code"].return_value = None

        response = await client.post(
            "/api/v1/join-requests/join-by-code", json={"joinCode": "BADCODE"}
        )
        assert response.status_code == 404
        assert "Invalid or expired" in response.json()["detail"]

    async def test_join_by_code_creates_pending_request(
        self, client, override_auth, mock_join_request_db
    ):
        user = override_auth(role="STUDENT")
        school_class = make_fake_school_class()
        mock_join_request_db["get_student_by_user_id"].return_value = None
        mock_join_request_db["get_class_by_join_code"].return_value = school_class
        mock_join_request_db[
            "create_or_reopen_join_request"
        ].return_value = make_request()

        response = await client.post(
            "/api/v1/join-requests/join-by-code", json={"joinCode": "class1a2"}
        )
        assert response.status_code == 201
        mock_join_request_db["get_class_by_join_code"].assert_awaited_once_with(
            "class1a2"
        )
        mock_join_request_db["create_or_reopen_join_request"].assert_awaited_once_with(
            user.id, school_class
        )

    async def test_duplicate_pending_request_is_rejected(
        self, client, override_auth, mock_join_request_db
    ):
        override_auth(role="STUDENT")
        mock_join_request_db["get_student_by_user_id"].return_value = None
        mock_join_request_db[
            "get_class_by_join_code"
        ].return_value = make_fake_school_class()
        mock_join_request_db["create_or_reopen_join_request"].side_effect = ValueError(
            "A join request for this class already exists"
        )

        response = await client.post(
            "/api/v1/join-requests/join-by-code", json={"joinCode": "CLASS1A2"}
        )
        assert response.status_code == 409

    async def test_student_can_see_own_request_status(
        self, client, override_auth, mock_join_request_db
    ):
        user = override_auth(role="STUDENT")
        mock_join_request_db["get_join_requests_for_user"].return_value = [
            make_request(status="REJECTED")
        ]

        response = await client.get("/api/v1/join-requests/me")
        assert response.status_code == 200
        assert response.json()[0]["status"] == "REJECTED"
        mock_join_request_db["get_join_requests_for_user"].assert_awaited_once_with(
            user.id
        )

    async def test_student_cannot_approve_request(
        self, client, override_auth, mock_join_request_db
    ):
        override_auth(role="STUDENT")
        request = type(
            "Request",
            (),
            {"id": "request_001", "schoolClass": make_fake_school_class()},
        )()
        mock_join_request_db["get_join_request_by_id"].return_value = request

        response = await client.patch(
            f"/api/v1/join-requests/{request.id}", json={"status": "APPROVED"}
        )
        assert response.status_code == 403
        mock_join_request_db["decide_join_request"].assert_not_awaited()

    async def test_other_school_teacher_cannot_approve(
        self, client, override_auth, mock_join_request_db
    ):
        override_auth(role="TEACHER")
        request = type(
            "Request",
            (),
            {
                "id": "request_001",
                "schoolClass": make_fake_school_class({"schoolId": "school_123"}),
            },
        )()
        mock_join_request_db["get_join_request_by_id"].return_value = request
        mock_join_request_db["get_teacher_by_user_id"].return_value = make_fake_teacher(
            {"schoolId": "school_456"}
        )

        response = await client.patch(
            f"/api/v1/join-requests/{request.id}", json={"status": "APPROVED"}
        )
        assert response.status_code == 403
        mock_join_request_db["decide_join_request"].assert_not_awaited()

    async def test_teacher_approval_uses_atomic_decision_service(
        self, client, override_auth, mock_join_request_db
    ):
        override_auth(role="TEACHER")
        request = type(
            "Request",
            (),
            {
                "id": "request_001",
                "schoolClass": make_fake_school_class({"schoolId": "school_123"}),
            },
        )()
        teacher = make_fake_teacher({"schoolId": "school_123"})
        mock_join_request_db["get_join_request_by_id"].return_value = request
        mock_join_request_db["get_teacher_by_user_id"].return_value = teacher
        mock_join_request_db["decide_join_request"].return_value = make_request(
            status="APPROVED"
        )

        response = await client.patch(
            f"/api/v1/join-requests/{request.id}", json={"status": "APPROVED"}
        )
        assert response.status_code == 200
        mock_join_request_db["decide_join_request"].assert_awaited_once_with(
            request.id, JoinRequestStatus.APPROVED, teacher.id
        )

    async def test_rejection_does_not_create_student_in_router(
        self, client, override_auth, mock_join_request_db
    ):
        override_auth(role="TEACHER")
        request = type(
            "Request",
            (),
            {
                "id": "request_001",
                "schoolClass": make_fake_school_class({"schoolId": "school_123"}),
            },
        )()
        teacher = make_fake_teacher({"schoolId": "school_123"})
        mock_join_request_db["get_join_request_by_id"].return_value = request
        mock_join_request_db["get_teacher_by_user_id"].return_value = teacher
        mock_join_request_db["decide_join_request"].return_value = make_request(
            status="REJECTED"
        )

        response = await client.patch(
            f"/api/v1/join-requests/{request.id}", json={"status": "REJECTED"}
        )
        assert response.status_code == 200
        mock_join_request_db["decide_join_request"].assert_awaited_once_with(
            request.id, JoinRequestStatus.REJECTED, teacher.id
        )


def test_roll_number_is_unique_per_class_at_the_model_layer():
    constraints = [
        constraint
        for constraint in Student.__table__.constraints
        if constraint.name == "student_classid_rollno_key"
    ]
    assert len(constraints) == 1
    assert [column.name for column in constraints[0].columns] == ["classId", "rollNo"]
    assert SchoolClass.nextRollNo.property.columns[0].default.arg == 1


class _Transaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False


def _decision_request():
    school_class = SimpleNamespace(
        id="class_001", name="12th - A", schoolId="school_001", nextRollNo=7
    )
    return SimpleNamespace(
        id="request_001",
        studentUserId="user_001",
        classId=school_class.id,
        status=JoinRequestStatus.PENDING,
        requestedAt=datetime.now(UTC),
        decidedAt=None,
        decidedBy=None,
        user=SimpleNamespace(name="Test User", email="student@example.com"),
        schoolClass=school_class,
    )


@pytest.mark.asyncio
async def test_approval_allocates_and_advances_a_class_roll_number_atomically():
    request = _decision_request()
    session = MagicMock()
    session.begin.return_value = _Transaction()
    session.scalar = AsyncMock(
        side_effect=[request, request.schoolClass, None, request]
    )

    result = await decide_join_request(
        request.id, JoinRequestStatus.APPROVED, "teacher_001", session=session
    )

    students = [
        call.args[0]
        for call in session.add.call_args_list
        if isinstance(call.args[0], Student)
    ]
    assert result.status == "APPROVED"
    assert len(students) == 1
    assert students[0].rollNo == "7"
    assert students[0].classId == "class_001"
    assert request.schoolClass.nextRollNo == 8


@pytest.mark.asyncio
async def test_rejection_creates_no_student_row():
    request = _decision_request()
    session = MagicMock()
    session.begin.return_value = _Transaction()
    session.scalar = AsyncMock(side_effect=[request, request.schoolClass, request])

    result = await decide_join_request(
        request.id, JoinRequestStatus.REJECTED, "teacher_001", session=session
    )

    created = [call.args[0] for call in session.add.call_args_list]
    assert result.status == "REJECTED"
    assert not any(isinstance(item, Student) for item in created)
    assert any(isinstance(item, Notification) for item in created)
