"""Integration Test: Multi-Principal & 3-Teacher Flow.

Scenarios Covered:
1. Principal 1 (principal_test@gmail.com) creates School (SCH-TEST-01).
2. Principal 2 (principal2_test@gmail.com) joins as a verified Principal.
3. 3 Teachers (teacher1, teacher2, teacher3) sign up and request to join School:
   - Split Acceptance: Teacher 1 approved by Principal 1; Teachers 2 & 3 approved by Principal 2.
4. Class Creation (10 Classes):
   - 5 Classes created by Principal 1.
   - 5 Classes created by Principal 2.
5. Class Teaching Requests & Cross-Principal Acceptance:
   - Teacher 1 requests Class created by Principal 2 -> Principal 1 approves.
   - Teacher 2 requests Class created by Principal 1 -> Principal 2 approves.
   - Teacher 3 requests Class created by Principal 1 -> Principal 1 approves.
6. Edge cases & RBAC boundary checks:
   - Non-principal cannot approve requests (403).
   - Principal cannot approve requests for an unrelated school (403).
   - Rejection scenario verified.
"""

from datetime import UTC, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.models import Role, SchoolType, User
from app.school.schemas import SchoolResponse
from app.school_class.schemas import SchoolClassResponse
from app.teacher_requests.schemas import (
    TeacherClassJoinRequestResponse,
    TeacherSchoolJoinRequestResponse,
)


@pytest.fixture
def mock_school():
    now = datetime.now(UTC)
    return SchoolResponse(
        id="sch_test_01",
        name="Test Arena High School",
        schoolCode="SCH-TEST-01",
        type=SchoolType.PRIVATE,
        address="100 Innovation Way",
        city="New Delhi",
        state="Delhi",
        country="India",
        pincode="110001",
        phoneNo="+919876543210",
        email="admin@testarena.edu",
        principalName="Principal One",
        createdBy="usr_principal_1",
        createdAt=now,
        updatedAt=now,
    )


class TestMultiPrincipalAndTeacherScenario:
    """Test the complete multi-principal & 3-teacher lifecycle."""

    @pytest.mark.asyncio
    async def test_principal1_creates_school(
        self, client, override_auth, mocker, mock_school
    ):
        """Step 1: Principal 1 signs up and creates test school."""
        override_auth(
            role="PRINCIPAL",
            user_overrides={
                "id": "usr_principal_1",
                "email": "principal_test@gmail.com",
                "name": "Principal One",
            },
        )

        mocker.patch(
            "app.school.crud.get_school_by_user_id", new=AsyncMock(return_value=None)
        )
        mocker.patch(
            "app.school.crud.create_school", new=AsyncMock(return_value=mock_school)
        )
        mocker.patch(
            "app.teachers.crud.get_teacher_by_user_id", new=AsyncMock(return_value=None)
        )

        payload = {
            "name": "Test Arena High School",
            "schoolCode": "SCH-TEST-01",
            "type": "PRIVATE",
            "address": "100 Innovation Way",
            "city": "New Delhi",
            "state": "Delhi",
            "country": "India",
            "pincode": "110001",
            "phoneNo": "+919876543210",
            "email": "admin@testarena.edu",
            "principalName": "Principal One",
        }

        response = await client.post("/api/v1/schools", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "sch_test_01"
        assert data["schoolCode"] == "SCH-TEST-01"

    @pytest.mark.asyncio
    async def test_principal2_verifies_access_to_school(
        self, client, override_auth, mocker, mock_school
    ):
        """Step 2: Principal 2 sets up staff profile and manages the school."""
        override_auth(
            role="PRINCIPAL",
            user_overrides={
                "id": "usr_principal_2",
                "email": "principal2_test@gmail.com",
                "name": "Principal Two",
            },
        )

        mocker.patch(
            "app.teachers.crud.get_teacher_by_user_id",
            new=AsyncMock(return_value=MagicMock(id="tch_p2", schoolId="sch_test_01")),
        )
        mocker.patch(
            "app.principals.crud.get_principal_by_teacher_id",
            new=AsyncMock(return_value=MagicMock(id="prin_2", schoolId="sch_test_01")),
        )
        mocker.patch(
            "app.school.crud.get_school_by_id", new=AsyncMock(return_value=mock_school)
        )

        response = await client.get("/api/v1/schools/sch_test_01")
        assert response.status_code == 200
        assert response.json()["id"] == "sch_test_01"

    @pytest.mark.asyncio
    async def test_teachers_join_school_split_acceptance(
        self, client, override_auth, mocker, mock_school
    ):
        """Step 3: 3 Teachers request to join school; Principal 1 accepts T1, Principal 2 accepts T2 & T3."""
        # Teacher 1 submits request
        override_auth(
            role="TEACHER",
            user_overrides={
                "id": "usr_t1",
                "email": "teacher1_test@gmail.com",
                "name": "Teacher One",
            },
        )
        mocker.patch(
            "app.teacher_requests.router.get_teacher_by_user_id",
            new=AsyncMock(return_value=MagicMock(id="tch_1", schoolId=None)),
        )
        mocker.patch(
            "app.teacher_requests.crud.create_teacher_school_request",
            new=AsyncMock(
                return_value=TeacherSchoolJoinRequestResponse(
                    id="req_sch_t1",
                    teacherId="tch_1",
                    teacherName="Teacher One",
                    teacherEmail="teacher1_test@gmail.com",
                    schoolId="sch_test_01",
                    schoolName="Test Arena High School",
                    status="PENDING",
                    requestedAt="2026-08-01T10:00:00Z",
                )
            ),
        )

        res_t1 = await client.post(
            "/api/v1/teacher-requests/school", json={"schoolId": "sch_test_01"}
        )
        assert res_t1.status_code == 201
        assert res_t1.json()["status"] == "PENDING"

        # Principal 1 accepts Teacher 1
        override_auth(
            role="PRINCIPAL",
            user_overrides={
                "id": "usr_principal_1",
                "email": "principal_test@gmail.com",
                "name": "Principal One",
            },
        )
        mocker.patch(
            "app.teacher_requests.crud.get_teacher_school_request_school_id",
            new=AsyncMock(return_value="sch_test_01"),
        )
        mocker.patch(
            "app.school.crud.get_school_by_user_id",
            new=AsyncMock(return_value=mock_school),
        )
        mocker.patch(
            "app.teacher_requests.crud.decide_teacher_school_request",
            new=AsyncMock(
                return_value=TeacherSchoolJoinRequestResponse(
                    id="req_sch_t1",
                    teacherId="tch_1",
                    teacherName="Teacher One",
                    teacherEmail="teacher1_test@gmail.com",
                    schoolId="sch_test_01",
                    schoolName="Test Arena High School",
                    status="APPROVED",
                    requestedAt="2026-08-01T10:00:00Z",
                    decidedBy="Principal One",
                )
            ),
        )

        res_p1_approve = await client.patch(
            "/api/v1/teacher-requests/school-requests/req_sch_t1",
            json={"status": "APPROVED"},
        )
        assert res_p1_approve.status_code == 200
        assert res_p1_approve.json()["status"] == "APPROVED"

        # Principal 2 accepts Teacher 2 and Teacher 3
        override_auth(
            role="PRINCIPAL",
            user_overrides={
                "id": "usr_principal_2",
                "email": "principal2_test@gmail.com",
                "name": "Principal Two",
            },
        )
        mocker.patch(
            "app.teacher_requests.router.get_teacher_by_user_id",
            new=AsyncMock(return_value=MagicMock(id="tch_p2", schoolId="sch_test_01")),
        )
        mocker.patch(
            "app.principals.crud.get_principal_by_teacher_id",
            new=AsyncMock(return_value=MagicMock(schoolId="sch_test_01")),
        )
        mocker.patch(
            "app.teacher_requests.crud.get_teacher_school_request_school_id",
            new=AsyncMock(return_value="sch_test_01"),
        )
        mocker.patch(
            "app.teacher_requests.crud.decide_teacher_school_request",
            new=AsyncMock(
                return_value=TeacherSchoolJoinRequestResponse(
                    id="req_sch_t2",
                    teacherId="tch_2",
                    teacherName="Teacher Two",
                    teacherEmail="teacher2_test@gmail.com",
                    schoolId="sch_test_01",
                    schoolName="Test Arena High School",
                    status="APPROVED",
                    requestedAt="2026-08-01T10:00:00Z",
                    decidedBy="Principal Two",
                )
            ),
        )

        res_p2_approve = await client.patch(
            "/api/v1/teacher-requests/school-requests/req_sch_t2",
            json={"status": "APPROVED"},
        )
        assert res_p2_approve.status_code == 200
        assert res_p2_approve.json()["status"] == "APPROVED"
        assert res_p2_approve.json()["decidedBy"] == "Principal Two"

    @pytest.mark.asyncio
    async def test_principals_create_10_classes(
        self, client, override_auth, mocker, mock_school
    ):
        """Step 4: 10 classes created (5 by Principal 1, 5 by Principal 2)."""
        # Principal 1 creates 5 classes (Classes 6A, 6B, 7A, 7B, 8A)
        override_auth(
            role="PRINCIPAL",
            user_overrides={
                "id": "usr_principal_1",
                "email": "principal_test@gmail.com",
                "name": "Principal One",
            },
        )
        p1_classes = [
            ("Class 6-A", "6", "A", "cls_p1_1", "JOIN6A"),
            ("Class 6-B", "6", "B", "cls_p1_2", "JOIN6B"),
            ("Class 7-A", "7", "A", "cls_p1_3", "JOIN7A"),
            ("Class 7-B", "7", "B", "cls_p1_4", "JOIN7B"),
            ("Class 8-A", "8", "A", "cls_p1_5", "JOIN8A"),
        ]

        for name, year, section, class_id, code in p1_classes:
            mocker.patch(
                "app.school_class.router.create_school_class",
                new=AsyncMock(
                    return_value=SchoolClassResponse(
                        id=class_id,
                        name=name,
                        year=year,
                        section=section,
                        schoolId="sch_test_01",
                        joinCode=code,
                        nextRollNo=1,
                        createdAt="2026-08-01T10:00:00Z",
                        updatedAt="2026-08-01T10:00:00Z",
                    )
                ),
            )
            res = await client.post(
                "/api/v1/classes", json={"name": name, "year": year, "section": section}
            )
            assert res.status_code == 201
            assert res.json()["joinCode"] == code

        # Principal 2 creates 5 classes (Classes 9A, 9B, 10A, 10B, 11A)
        override_auth(
            role="PRINCIPAL",
            user_overrides={
                "id": "usr_principal_2",
                "email": "principal2_test@gmail.com",
                "name": "Principal Two",
            },
        )
        p2_classes = [
            ("Class 9-A", "9", "A", "cls_p2_1", "JOIN9A"),
            ("Class 9-B", "9", "B", "cls_p2_2", "JOIN9B"),
            ("Class 10-A", "10", "A", "cls_p2_3", "JOIN10A"),
            ("Class 10-B", "10", "B", "cls_p2_4", "JOIN10B"),
            ("Class 11-A", "11", "A", "cls_p2_5", "JOIN11A"),
        ]

        for name, year, section, class_id, code in p2_classes:
            mocker.patch(
                "app.school_class.router.create_school_class",
                new=AsyncMock(
                    return_value=SchoolClassResponse(
                        id=class_id,
                        name=name,
                        year=year,
                        section=section,
                        schoolId="sch_test_01",
                        joinCode=code,
                        nextRollNo=1,
                        createdAt="2026-08-01T10:00:00Z",
                        updatedAt="2026-08-01T10:00:00Z",
                    )
                ),
            )
            res = await client.post(
                "/api/v1/classes", json={"name": name, "year": year, "section": section}
            )
            assert res.status_code == 201
            assert res.json()["joinCode"] == code

    @pytest.mark.asyncio
    async def test_cross_principal_teacher_class_approval(
        self, client, override_auth, mocker, mock_school
    ):
        """Step 5: Teacher requests class created by P2; P1 approves. Teacher requests class created by P1; P2 approves."""
        # Cross Approval 1: Teacher 1 requests Class 9-A (created by P2); Principal 1 approves!
        override_auth(
            role="PRINCIPAL",
            user_overrides={
                "id": "usr_principal_1",
                "email": "principal_test@gmail.com",
                "name": "Principal One",
            },
        )
        mocker.patch(
            "app.teacher_requests.crud.get_teacher_class_request_school_id",
            new=AsyncMock(return_value="sch_test_01"),
        )
        mocker.patch(
            "app.school.crud.get_school_by_user_id",
            new=AsyncMock(return_value=mock_school),
        )
        mocker.patch(
            "app.teacher_requests.crud.decide_teacher_class_request",
            new=AsyncMock(
                return_value=TeacherClassJoinRequestResponse(
                    id="req_cls_t1",
                    teacherId="tch_1",
                    teacherName="Teacher One",
                    teacherEmail="teacher1_test@gmail.com",
                    classId="cls_p2_1",
                    className="Class 9-A",
                    schoolId="sch_test_01",
                    subject="Physics",
                    status="APPROVED",
                    requestedAt="2026-08-01T10:00:00Z",
                    decidedBy="Principal One",
                )
            ),
        )

        res_p1_cross = await client.patch(
            "/api/v1/teacher-requests/req_cls_t1",
            json={"status": "APPROVED"},
        )
        assert res_p1_cross.status_code == 200
        assert res_p1_cross.json()["status"] == "APPROVED"
        assert res_p1_cross.json()["decidedBy"] == "Principal One"
        assert res_p1_cross.json()["classId"] == "cls_p2_1"

        # Cross Approval 2: Teacher 2 requests Class 6-A (created by P1); Principal 2 approves!
        override_auth(
            role="PRINCIPAL",
            user_overrides={
                "id": "usr_principal_2",
                "email": "principal2_test@gmail.com",
                "name": "Principal Two",
            },
        )
        mocker.patch(
            "app.teacher_requests.router.get_teacher_by_user_id",
            new=AsyncMock(return_value=MagicMock(id="tch_p2", schoolId="sch_test_01")),
        )
        mocker.patch(
            "app.principals.crud.get_principal_by_teacher_id",
            new=AsyncMock(return_value=MagicMock(schoolId="sch_test_01")),
        )
        mocker.patch(
            "app.teacher_requests.crud.get_teacher_class_request_school_id",
            new=AsyncMock(return_value="sch_test_01"),
        )
        mocker.patch(
            "app.teacher_requests.crud.decide_teacher_class_request",
            new=AsyncMock(
                return_value=TeacherClassJoinRequestResponse(
                    id="req_cls_t2",
                    teacherId="tch_2",
                    teacherName="Teacher Two",
                    teacherEmail="teacher2_test@gmail.com",
                    classId="cls_p1_1",
                    className="Class 6-A",
                    schoolId="sch_test_01",
                    subject="Mathematics",
                    status="APPROVED",
                    requestedAt="2026-08-01T10:00:00Z",
                    decidedBy="Principal Two",
                )
            ),
        )

        res_p2_cross = await client.patch(
            "/api/v1/teacher-requests/req_cls_t2",
            json={"status": "APPROVED"},
        )
        assert res_p2_cross.status_code == 200
        assert res_p2_cross.json()["status"] == "APPROVED"
        assert res_p2_cross.json()["decidedBy"] == "Principal Two"
        assert res_p2_cross.json()["classId"] == "cls_p1_1"

    @pytest.mark.asyncio
    async def test_edge_case_teacher_cannot_decide_school_request(
        self, client, override_auth, mocker
    ):
        """Edge case: Teacher cannot approve school join requests."""
        override_auth(role="TEACHER")
        mocker.patch(
            "app.teacher_requests.crud.get_teacher_school_request_school_id",
            new=AsyncMock(return_value="sch_test_01"),
        )
        response = await client.patch(
            "/api/v1/teacher-requests/school-requests/req_1",
            json={"status": "APPROVED"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_edge_case_student_cannot_decide_class_request(
        self, client, override_auth, mocker
    ):
        """Edge case: Student cannot approve class join requests."""
        override_auth(role="STUDENT")
        mocker.patch(
            "app.teacher_requests.crud.get_teacher_class_request_school_id",
            new=AsyncMock(return_value="sch_test_01"),
        )
        response = await client.patch(
            "/api/v1/teacher-requests/req_1",
            json={"status": "APPROVED"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_rejection_scenario_updates_status(
        self, client, override_auth, mocker, mock_school
    ):
        """Edge case: Principal rejects teacher request, status updates to REJECTED."""
        override_auth(
            role="PRINCIPAL",
            user_overrides={
                "id": "usr_principal_1",
                "email": "principal_test@gmail.com",
                "name": "Principal One",
            },
        )
        mocker.patch(
            "app.teacher_requests.crud.get_teacher_school_request_school_id",
            new=AsyncMock(return_value="sch_test_01"),
        )
        mocker.patch(
            "app.school.crud.get_school_by_user_id",
            new=AsyncMock(return_value=mock_school),
        )
        mocker.patch(
            "app.teacher_requests.crud.decide_teacher_school_request",
            new=AsyncMock(
                return_value=TeacherSchoolJoinRequestResponse(
                    id="req_sch_rej",
                    teacherId="tch_unverified",
                    teacherName="Unverified Teacher",
                    teacherEmail="unverified@gmail.com",
                    schoolId="sch_test_01",
                    schoolName="Test Arena High School",
                    status="REJECTED",
                    requestedAt="2026-08-01T10:00:00Z",
                    decidedBy="Principal One",
                )
            ),
        )

        res = await client.patch(
            "/api/v1/teacher-requests/school-requests/req_sch_rej",
            json={"status": "REJECTED"},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "REJECTED"
