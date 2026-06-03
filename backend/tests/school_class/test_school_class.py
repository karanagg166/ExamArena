# backend/tests/school_class/test_school_class.py
import pytest
from unittest.mock import MagicMock
from tests.dummy_data.schools import make_fake_school_class
from tests.dummy_data.students import make_fake_student
from tests.dummy_data.teachers import make_fake_teacher, make_fake_principal

@pytest.mark.asyncio
class TestSchoolClassesApi:

    async def test_create_success(self, client, override_auth, mock_class_db):
        override_auth(role="PRINCIPAL")
        fake_class = make_fake_school_class()
        mock_class_db["create_school_class"].return_value = fake_class

        payload = {
            "name": "12th - A",
            "year": "12th",
            "section": "A"
        }
        response = await client.post("/api/v1/classes", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == fake_class.id
        assert data["name"] == fake_class.name

    async def test_create_forbidden(self, client, override_auth, mock_class_db):
        override_auth(role="PRINCIPAL")
        mock_class_db["create_school_class"].return_value = None

        payload = {
            "name": "12th - A",
            "year": "12th",
            "section": "A"
        }
        response = await client.post("/api/v1/classes", json=payload)
        assert response.status_code == 403
        assert "only create classes for your own school" in response.json()["detail"]

    async def test_list_by_school(self, client, override_auth, mock_class_db):
        override_auth(role="STUDENT")
        fake_class = make_fake_school_class()
        mock_class_db["get_school_classes_by_school_id"].return_value = [fake_class]

        response = await client.get("/api/v1/classes/school/school_001")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == fake_class.id

    async def test_class_not_found(self, client, override_auth, mock_class_db):
        override_auth(role="STUDENT")
        mock_class_db["get_school_class_by_id"].return_value = None

        response = await client.get("/api/v1/classes/clxfake_class_999")
        assert response.status_code == 404
        assert "Class not found" in response.json()["detail"]

    async def test_student_own_class(self, client, override_auth, mock_class_db):
        user = override_auth(role="STUDENT")
        fake_class = make_fake_school_class()
        mock_class_db["get_school_class_by_id"].return_value = fake_class
        
        student = make_fake_student({"classId": fake_class.id})
        mock_class_db["get_student_by_user_id"].return_value = student

        response = await client.get(f"/api/v1/classes/{fake_class.id}")
        assert response.status_code == 200
        assert response.json()["id"] == fake_class.id

    async def test_student_other_class(self, client, override_auth, mock_class_db):
        user = override_auth(role="STUDENT")
        fake_class = make_fake_school_class()
        mock_class_db["get_school_class_by_id"].return_value = fake_class
        
        student = make_fake_student({"classId": "other_class"})
        mock_class_db["get_student_by_user_id"].return_value = student

        response = await client.get(f"/api/v1/classes/{fake_class.id}")
        assert response.status_code == 403
        assert "Access denied. You can only view your own class." in response.json()["detail"]

    async def test_teacher_same_school(self, client, override_auth, mock_class_db):
        override_auth(role="TEACHER")
        fake_class = make_fake_school_class({"schoolId": "school_123"})
        mock_class_db["get_school_class_by_id"].return_value = fake_class
        
        teacher = make_fake_teacher({"schoolId": "school_123"})
        mock_class_db["get_teacher_by_user_id"].return_value = teacher

        response = await client.get(f"/api/v1/classes/{fake_class.id}")
        assert response.status_code == 200

    async def test_teacher_diff_school(self, client, override_auth, mock_class_db):
        override_auth(role="TEACHER")
        fake_class = make_fake_school_class({"schoolId": "school_123"})
        mock_class_db["get_school_class_by_id"].return_value = fake_class
        
        teacher = make_fake_teacher({"schoolId": "school_456"})
        mock_class_db["get_teacher_by_user_id"].return_value = teacher

        response = await client.get(f"/api/v1/classes/{fake_class.id}")
        assert response.status_code == 403
        assert "You must be a teacher at this school" in response.json()["detail"]

    async def test_students_success(self, client, override_auth, mock_class_db):
        override_auth(role="TEACHER")
        fake_class = make_fake_school_class({"schoolId": "school_123"})
        mock_class_db["get_school_class_by_id"].return_value = fake_class
        
        teacher = make_fake_teacher({"schoolId": "school_123"})
        mock_class_db["get_teacher_by_user_id"].return_value = teacher
        
        fake_student = make_fake_student()
        mock_class_db["get_students_by_class_id"].return_value = [fake_student]

        response = await client.get(f"/api/v1/classes/{fake_class.id}/students")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == fake_student.id

    async def test_students_class_not_found(self, client, override_auth, mock_class_db):
        override_auth(role="TEACHER")
        mock_class_db["get_school_class_by_id"].return_value = None

        response = await client.get("/api/v1/classes/clxfake_class_999/students")
        assert response.status_code == 404
        assert "Class not found" in response.json()["detail"]

    async def test_students_student_own_class(self, client, override_auth, mock_class_db):
        override_auth(role="STUDENT")
        fake_class = make_fake_school_class()
        mock_class_db["get_school_class_by_id"].return_value = fake_class
        
        student = make_fake_student({"classId": fake_class.id})
        mock_class_db["get_student_by_user_id"].return_value = student
        mock_class_db["get_students_by_class_id"].return_value = [student]

        response = await client.get(f"/api/v1/classes/{fake_class.id}/students")
        assert response.status_code == 200

    async def test_students_student_other_class(self, client, override_auth, mock_class_db):
        override_auth(role="STUDENT")
        fake_class = make_fake_school_class()
        mock_class_db["get_school_class_by_id"].return_value = fake_class
        
        student = make_fake_student({"classId": "other_class"})
        mock_class_db["get_student_by_user_id"].return_value = student

        response = await client.get(f"/api/v1/classes/{fake_class.id}/students")
        assert response.status_code == 403
        assert "Access denied. You can only view your own class." in response.json()["detail"]
