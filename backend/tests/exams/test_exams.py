import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
from tests.dummy_data.exams import make_fake_exam, make_fake_student_exam
from tests.dummy_data.teachers import make_fake_teacher
from tests.dummy_data.students import make_fake_student

def make_teacher_info_dict():
    return {
        "id": "clxfake_teacher_001",
        "user": {"name": "Teacher User"},
        "school": {"name": "Test School"}
    }

def make_student_exam_dict():
    return {
        "id": "clxfake_exam_001",
        "name": "Midterm Maths",
        "description": "Test description",
        "scheduledAt": datetime(2026, 1, 1),
        "duration": 60,
        "maxMarks": 100,
        "isPublished": True,
        "type": "MIDTERM",
        "createdAt": datetime(2026, 1, 1),
        "updatedAt": datetime(2026, 1, 1),
        "teacher": make_teacher_info_dict(),
        "questions": [],
        "studentStatus": "IN_PROGRESS",
        "attemptId": "clxfake_se_001"
    }

@pytest.mark.asyncio
class TestExamsApi:

    # ── POST /api/v1/exams ─────────────────────────────────────
    async def test_create_exam_success(self, client, override_auth, mock_exams_db):
        override_auth(role="TEACHER")
        fake_teacher = make_fake_teacher()
        mock_exams_db["get_teacher_by_user_id"].return_value = fake_teacher
        
        fake_exam = make_fake_exam()
        mock_exams_db["create_exam"].return_value = fake_exam

        payload = {
            "name": "Midterm Maths",
            "description": "Test description",
            "scheduledAt": "2026-06-03T14:44:52Z",
            "duration": 60,
            "maxMarks": 100,
            "type": "MIDTERM",
            "isPublished": False
        }
        response = await client.post("/api/v1/exams", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == fake_exam.id

    async def test_create_exam_not_teacher(self, client, override_auth, mock_exams_db):
        override_auth(role="STUDENT")
        mock_exams_db["get_teacher_by_user_id"].return_value = None

        payload = {
            "name": "Midterm Maths",
            "description": "Test description",
            "scheduledAt": "2026-06-03T14:44:52Z",
            "duration": 60,
            "maxMarks": 100,
            "type": "MIDTERM",
            "isPublished": False
        }
        response = await client.post("/api/v1/exams", json=payload)
        assert response.status_code == 403
        assert "Only teachers can manage exams" in response.json()["detail"]

    async def test_create_exam_crud_exception(self, client, override_auth, mock_exams_db):
        override_auth(role="TEACHER")
        mock_exams_db["get_teacher_by_user_id"].return_value = make_fake_teacher()
        mock_exams_db["create_exam"].side_effect = Exception("Database error")

        payload = {
            "name": "Midterm Maths",
            "description": "Test description",
            "scheduledAt": "2026-06-03T14:44:52Z",
            "duration": 60,
            "maxMarks": 100,
            "type": "MIDTERM",
            "isPublished": False
        }
        response = await client.post("/api/v1/exams", json=payload)
        assert response.status_code == 500
        assert "Failed to create exam" in response.json()["detail"]

    # ── GET /api/v1/exams ──────────────────────────────────────
    async def test_list_my_exams_success(self, client, override_auth, mock_exams_db):
        override_auth(role="TEACHER")
        mock_exams_db["get_teacher_by_user_id"].return_value = make_fake_teacher()
        fake_exam = make_fake_exam()
        mock_exams_db["get_exams_by_teacher"].return_value = [fake_exam]

        response = await client.get("/api/v1/exams")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == fake_exam.id

    async def test_list_my_exams_not_teacher(self, client, override_auth, mock_exams_db):
        override_auth(role="STUDENT")
        mock_exams_db["get_teacher_by_user_id"].return_value = None

        response = await client.get("/api/v1/exams")
        assert response.status_code == 403

    # ── GET /api/v1/exams/public ───────────────────────────────
    async def test_public_as_teacher(self, client, override_auth, mock_exams_db):
        override_auth(role="TEACHER")
        teacher = make_fake_teacher({"schoolId": "school_123"})
        mock_exams_db["get_teacher_by_user_id"].return_value = teacher
        
        fake_exam = make_fake_exam()
        mock_exams_db["get_published_exams"].return_value = [fake_exam]

        response = await client.get("/api/v1/exams/public")
        assert response.status_code == 200
        mock_exams_db["get_published_exams"].assert_called_once_with(
            name=None,
            exam_type=None,
            teacher_name=None,
            school_name=None,
            subject=None,
            school_id="school_123"
        )

    async def test_public_as_student(self, client, override_auth, mock_exams_db):
        override_auth(role="STUDENT")
        fake_exam = make_fake_exam()
        mock_exams_db["get_published_exams"].return_value = [fake_exam]

        response = await client.get("/api/v1/exams/public")
        assert response.status_code == 200
        mock_exams_db["get_published_exams"].assert_called_once_with(
            name=None,
            exam_type=None,
            teacher_name=None,
            school_name=None,
            subject=None,
            school_id=None
        )

    async def test_public_with_filters(self, client, override_auth, mock_exams_db):
        override_auth(role="STUDENT")
        mock_exams_db["get_published_exams"].return_value = []

        response = await client.get("/api/v1/exams/public?name=maths&type=MIDTERM&subject=MATHS")
        assert response.status_code == 200
        mock_exams_db["get_published_exams"].assert_called_once_with(
            name="maths",
            exam_type="MIDTERM",
            teacher_name=None,
            school_name=None,
            subject="MATHS",
            school_id=None
        )

    # ── GET /api/v1/exams/student ──────────────────────────────
    async def test_student_exams_success(self, client, override_auth, mock_exams_db):
        override_auth(role="STUDENT")
        student = make_fake_student({"schoolId": "school_123"})
        mock_exams_db["student_crud_get_student_by_user_id"].return_value = student
        
        exam_dict = make_student_exam_dict()
        mock_exams_db["get_published_exams_for_student"].return_value = [exam_dict]

        response = await client.get("/api/v1/exams/student")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == exam_dict["id"]
        assert data[0]["studentStatus"] == "IN_PROGRESS"

    async def test_student_exams_not_student(self, client, override_auth, mock_exams_db):
        override_auth(role="TEACHER")

        response = await client.get("/api/v1/exams/student")
        assert response.status_code == 403

    async def test_student_exams_no_profile(self, client, override_auth, mock_exams_db):
        override_auth(role="STUDENT")
        mock_exams_db["student_crud_get_student_by_user_id"].return_value = None

        response = await client.get("/api/v1/exams/student")
        assert response.status_code == 400
        assert "Student profile not found" in response.json()["detail"]

    # ── GET /api/v1/exams/{exam_id} ─────────────────────────────
    async def test_get_exam_teacher(self, client, override_auth, mock_exams_db):
        override_auth(role="TEACHER")
        fake_exam = make_fake_exam()
        mock_exams_db["get_exam_by_id"].return_value = fake_exam

        response = await client.get(f"/api/v1/exams/{fake_exam.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == fake_exam.id

    async def test_get_exam_not_found(self, client, override_auth, mock_exams_db):
        override_auth(role="TEACHER")
        mock_exams_db["get_exam_by_id"].return_value = None

        response = await client.get("/api/v1/exams/clxfake_exam_999")
        assert response.status_code == 404
        assert "Exam not found" in response.json()["detail"]

    async def test_get_exam_student_strips_questions(self, client, override_auth, mock_exams_db):
        override_auth(role="STUDENT")
        student = make_fake_student()
        mock_exams_db["student_crud_get_student_by_user_id"].return_value = student
        
        # Mock exam with a mock question
        q1 = MagicMock()
        q1.id = "q1"
        q1.text = "Question 1"
        fake_exam = make_fake_exam({"questions": [q1]})
        mock_exams_db["get_exam_by_id"].return_value = fake_exam
        
        # Student hasn't started exam yet -> studentexam.find_unique returns None
        mock_exams_db["prisma"].studentexam.find_unique = AsyncMock(return_value=None)

        response = await client.get(f"/api/v1/exams/{fake_exam.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == fake_exam.id
        assert data["questionCount"] == 1
        assert data["questions"] == []  # stripped!

    # ── PATCH /api/v1/exams/{exam_id} ───────────────────────────
    async def test_patch_success(self, client, override_auth, mock_exams_db):
        override_auth(role="TEACHER")
        teacher = make_fake_teacher()
        mock_exams_db["get_teacher_by_user_id"].return_value = teacher
        
        fake_exam = make_fake_exam({"teacherId": teacher.id})
        # Note: exam.teacher.id must match teacher.id
        fake_exam.teacher.id = teacher.id
        mock_exams_db["get_exam_by_id"].return_value = fake_exam
        
        updated_exam = make_fake_exam({"name": "Updated Name"})
        mock_exams_db["update_exam"].return_value = updated_exam

        response = await client.patch(f"/api/v1/exams/{fake_exam.id}", json={"name": "Updated Name"})
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    async def test_patch_not_found(self, client, override_auth, mock_exams_db):
        override_auth(role="TEACHER")
        mock_exams_db["get_teacher_by_user_id"].return_value = make_fake_teacher()
        mock_exams_db["get_exam_by_id"].return_value = None

        response = await client.patch("/api/v1/exams/clxfake_exam_999", json={"name": "Updated Name"})
        assert response.status_code == 404

    async def test_patch_not_owner(self, client, override_auth, mock_exams_db):
        override_auth(role="TEACHER")
        teacher = make_fake_teacher({"id": "teacher_1"})
        mock_exams_db["get_teacher_by_user_id"].return_value = teacher
        
        fake_exam = make_fake_exam()
        fake_exam.teacher.id = "teacher_2"  # other teacher owner
        mock_exams_db["get_exam_by_id"].return_value = fake_exam

        response = await client.patch(f"/api/v1/exams/{fake_exam.id}", json={"name": "Updated Name"})
        assert response.status_code == 403
