import pytest
from unittest.mock import MagicMock
from tests.dummy_data.students import make_fake_student
from tests.dummy_data.teachers import make_fake_teacher, make_fake_principal
from app.students.schemas import StudentListItemResponse

@pytest.mark.asyncio
class TestStudentsApi:

    # ── Fetch Students ─────────────────────────────────────────
    async def test_fetch_as_student_scoped_to_class(self, client, override_auth, mock_student_db):
        user = override_auth(role="STUDENT")
        me = make_fake_student({"userId": user.id})
        mock_student_db["get_student_by_user_id"].return_value = me
        
        student_item = StudentListItemResponse(
            id="stu_item_1",
            userId="clxfake000000testuser",
            rollNo="STU001",
            classId="class_123",
            schoolId="school_123",
            name="Test User",
            email="testuser@examarena.dev",
            phoneNo="9999999999",
        )
        mock_student_db["get_students"].return_value = [student_item]

        response = await client.get("/api/v1/students")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        
        # Verify that get_students was called with scopeClassId and scopeSchoolId
        args, kwargs = mock_student_db["get_students"].call_args
        filter_params = args[0]
        assert filter_params.scopeClassId == me.classId
        assert filter_params.scopeSchoolId == me.schoolId

    async def test_fetch_as_student_no_profile(self, client, override_auth, mock_student_db):
        override_auth(role="STUDENT")
        mock_student_db["get_student_by_user_id"].return_value = None

        response = await client.get("/api/v1/students")
        assert response.status_code == 403
        assert "Student profile not found" in response.json()["detail"]

    async def test_fetch_as_teacher_scoped_to_school(self, client, override_auth, mock_student_db):
        override_auth(role="TEACHER")
        teacher = make_fake_teacher({"schoolId": "school_123"})
        mock_student_db["get_teacher_by_user_id"].return_value = teacher
        mock_student_db["get_students"].return_value = []

        response = await client.get("/api/v1/students")
        assert response.status_code == 200
        
        args, _ = mock_student_db["get_students"].call_args
        filter_params = args[0]
        assert filter_params.scopeSchoolId == "school_123"

    async def test_fetch_as_teacher_no_school(self, client, override_auth, mock_student_db):
        override_auth(role="TEACHER")
        teacher = make_fake_teacher({"schoolId": None})
        mock_student_db["get_teacher_by_user_id"].return_value = teacher

        response = await client.get("/api/v1/students")
        assert response.status_code == 403
        assert "You must be assigned to a school" in response.json()["detail"]

    async def test_fetch_as_admin_unscoped(self, client, override_auth, mock_student_db):
        override_auth(role="ADMIN")
        mock_student_db["get_students"].return_value = []

        response = await client.get("/api/v1/students")
        assert response.status_code == 200
        
        args, _ = mock_student_db["get_students"].call_args
        filter_params = args[0]
        assert filter_params.scopeSchoolId is None
        assert filter_params.scopeClassId is None

    # ── Create Student ─────────────────────────────────────────
    async def test_create_success(self, client, override_auth, mock_student_db):
        user = override_auth(role="STUDENT")
        mock_student_db["get_student_by_user_id"].return_value = None
        
        fake_student = make_fake_student({"userId": user.id})
        mock_student_db["create_student"].return_value = fake_student

        payload = {
            "rollNo": "STU001",
            "parentName": "Parent User",
            "parentEmail": "parent@test.dev",
            "classId": "class_001",
            "schoolId": "school_001"
        }
        response = await client.post("/api/v1/students", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["rollNo"] == "STU001"

    async def test_create_duplicate_profile(self, client, override_auth, mock_student_db):
        override_auth(role="STUDENT")
        mock_student_db["get_student_by_user_id"].return_value = make_fake_student()

        payload = {
            "rollNo": "STU001",
            "parentName": "Parent User",
            "parentEmail": "parent@test.dev",
            "classId": "class_001",
            "schoolId": "school_001"
        }
        response = await client.post("/api/v1/students", json=payload)
        assert response.status_code == 409
        assert "Student profile already exists" in response.json()["detail"]

    async def test_create_missing_fields(self, client, override_auth, mock_student_db):
        override_auth(role="STUDENT")
        # rollNo is required (omit it)
        payload = {
            "parentName": "Parent User",
            "parentEmail": "parent@test.dev",
            "classId": "class_001",
            "schoolId": "school_001"
        }
        response = await client.post("/api/v1/students", json=payload)
        assert response.status_code == 422

    # ── Get Me / Update Me ─────────────────────────────────────
    async def test_get_me_success(self, client, override_auth, mock_student_db):
        user = override_auth(role="STUDENT")
        fake_student = make_fake_student({"userId": user.id})
        mock_student_db["get_student_by_user_id"].return_value = fake_student

        response = await client.get("/api/v1/students/me")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == fake_student.id

    async def test_get_me_not_found(self, client, override_auth, mock_student_db):
        override_auth(role="STUDENT")
        mock_student_db["get_student_by_user_id"].return_value = None

        response = await client.get("/api/v1/students/me")
        assert response.status_code == 404
        assert "Student profile not found" in response.json()["detail"]

    async def test_update_me_success(self, client, override_auth, mock_student_db):
        user = override_auth(role="STUDENT")
        fake_student = make_fake_student({"userId": user.id})
        mock_student_db["get_student_by_user_id"].return_value = fake_student
        
        updated_student = make_fake_student({"userId": user.id, "parentName": "Updated Parent"})
        mock_student_db["update_student"].return_value = updated_student

        response = await client.put("/api/v1/students/me", json={"parentName": "Updated Parent"})
        assert response.status_code == 200
        data = response.json()
        assert data["parentName"] == "Updated Parent"

    async def test_update_me_not_found(self, client, override_auth, mock_student_db):
        override_auth(role="STUDENT")
        mock_student_db["get_student_by_user_id"].return_value = None

        response = await client.put("/api/v1/students/me", json={"parentName": "Updated Parent"})
        assert response.status_code == 404
        assert "Student profile not found" in response.json()["detail"]

    # ── Get Student By ID RBAC ────────────────────────────────
    async def test_not_found(self, client, override_auth, mock_student_db):
        override_auth(role="STUDENT")
        mock_student_db["get_student_by_id"].return_value = None

        response = await client.get("/api/v1/students/clxfake_student_999")
        assert response.status_code == 404
        assert "Student not found" in response.json()["detail"]

    async def test_student_views_own_profile(self, client, override_auth, mock_student_db):
        user = override_auth(role="STUDENT")
        fake_student = make_fake_student({"userId": user.id})
        mock_student_db["get_student_by_id"].return_value = fake_student
        mock_student_db["get_student_by_user_id"].return_value = fake_student

        response = await client.get(f"/api/v1/students/{fake_student.id}")
        assert response.status_code == 200
        assert response.json()["id"] == fake_student.id

    async def test_student_views_same_class_peer(self, client, override_auth, mock_student_db):
        user = override_auth(role="STUDENT")
        me = make_fake_student({"userId": user.id, "classId": "class_123"})
        peer = make_fake_student({"id": "student_peer", "userId": "user_peer", "classId": "class_123"})
        
        mock_student_db["get_student_by_id"].return_value = peer
        mock_student_db["get_student_by_user_id"].return_value = me

        response = await client.get(f"/api/v1/students/{peer.id}")
        assert response.status_code == 200

    async def test_student_views_different_class(self, client, override_auth, mock_student_db):
        user = override_auth(role="STUDENT")
        me = make_fake_student({"userId": user.id, "classId": "class_123"})
        other = make_fake_student({"id": "student_other", "userId": "user_other", "classId": "class_456"})
        
        mock_student_db["get_student_by_id"].return_value = other
        mock_student_db["get_student_by_user_id"].return_value = me

        response = await client.get(f"/api/v1/students/{other.id}")
        assert response.status_code == 403
        assert "You can only view profiles of students in your class" in response.json()["detail"]

    async def test_teacher_same_school(self, client, override_auth, mock_student_db):
        override_auth(role="TEACHER")
        teacher = make_fake_teacher({"schoolId": "school_123"})
        student = make_fake_student({"schoolId": "school_123"})
        
        mock_student_db["get_teacher_by_user_id"].return_value = teacher
        mock_student_db["get_student_by_id"].return_value = student

        response = await client.get(f"/api/v1/students/{student.id}")
        assert response.status_code == 200

    async def test_teacher_different_school(self, client, override_auth, mock_student_db):
        override_auth(role="TEACHER")
        teacher = make_fake_teacher({"schoolId": "school_123"})
        student = make_fake_student({"schoolId": "school_456"})
        
        mock_student_db["get_teacher_by_user_id"].return_value = teacher
        mock_student_db["get_student_by_id"].return_value = student

        response = await client.get(f"/api/v1/students/{student.id}")
        assert response.status_code == 403
        assert "You must be a teacher at this student's school" in response.json()["detail"]

    async def test_principal_same_school(self, client, override_auth, mock_student_db):
        override_auth(role="PRINCIPAL")
        teacher = make_fake_teacher({"schoolId": "school_123"})
        principal = make_fake_principal({"schoolId": "school_123", "teacherId": teacher.id})
        student = make_fake_student({"schoolId": "school_123"})
        
        mock_student_db["get_teacher_by_user_id"].return_value = teacher
        mock_student_db["get_principal_by_teacher_id"].return_value = principal
        mock_student_db["get_student_by_id"].return_value = student

        response = await client.get(f"/api/v1/students/{student.id}")
        assert response.status_code == 200
