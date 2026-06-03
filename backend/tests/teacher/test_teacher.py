# backend/tests/teacher/test_teacher.py
import pytest
from unittest.mock import MagicMock
from tests.dummy_data.teachers import make_fake_teacher

@pytest.mark.asyncio
class TestTeachersApi:

    async def test_fetch_teachers_success(self, client, override_auth, mock_teacher_db):
        override_auth(role="STUDENT")
        fake_teacher = make_fake_teacher()
        
        # Build list response dict / mock object
        teacher_item = MagicMock()
        teacher_item.id = fake_teacher.id
        teacher_item.name = fake_teacher.user.name
        teacher_item.email = fake_teacher.user.email
        teacher_item.phoneNo = fake_teacher.user.phoneNo
        teacher_item.experience = fake_teacher.experience
        teacher_item.qualifications = ["BACHELORS"]
        teacher_item.department = fake_teacher.department
        teacher_item.subjects = ["MATHS", "SCIENCE"]
        
        mock_teacher_db["get_teachers"].return_value = [teacher_item]

        response = await client.get("/api/v1/teachers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == fake_teacher.id
        assert data[0]["name"] == fake_teacher.user.name

    async def test_fetch_teachers_unauthenticated(self, client, mock_teacher_db):
        response = await client.get("/api/v1/teachers")
        assert response.status_code == 401

    async def test_create_success(self, client, override_auth, mock_teacher_db):
        override_auth(role="TEACHER")
        mock_teacher_db["get_teacher_by_user_id"].return_value = None
        fake_teacher = make_fake_teacher()
        mock_teacher_db["create_teacher"].return_value = fake_teacher

        payload = {
            "qualifications": ["BACHELORS"],
            "experience": 5,
            "department": "Science",
            "subjects": ["MATHS", "SCIENCE"]
        }
        response = await client.post("/api/v1/teachers", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == fake_teacher.id
        assert "qualifications" in data
        assert "subjects" in data

    async def test_create_duplicate(self, client, override_auth, mock_teacher_db):
        override_auth(role="TEACHER")
        mock_teacher_db["get_teacher_by_user_id"].return_value = make_fake_teacher()

        payload = {
            "qualifications": ["BACHELORS"],
            "experience": 5,
            "department": "Science",
            "subjects": ["MATHS"]
        }
        response = await client.post("/api/v1/teachers", json=payload)
        assert response.status_code == 409
        assert "Teacher profile already exists" in response.json()["detail"]

    async def test_create_missing_fields(self, client, override_auth, mock_teacher_db):
        override_auth(role="TEACHER")
        # experience is required (omit it)
        payload = {
            "qualifications": ["BACHELORS"],
            "department": "Science",
            "subjects": ["MATHS"]
        }
        response = await client.post("/api/v1/teachers", json=payload)
        assert response.status_code == 422

    async def test_get_me_success(self, client, override_auth, mock_teacher_db):
        override_auth(role="TEACHER")
        fake_teacher = make_fake_teacher()
        mock_teacher_db["get_teacher_by_user_id"].return_value = fake_teacher

        response = await client.get("/api/v1/teachers/me")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == fake_teacher.id
        assert data["qualifications"] == ["BACHELORS"]
        assert data["subjects"] == ["MATHS", "SCIENCE"]

    async def test_get_me_not_found(self, client, override_auth, mock_teacher_db):
        override_auth(role="TEACHER")
        mock_teacher_db["get_teacher_by_user_id"].return_value = None

        response = await client.get("/api/v1/teachers/me")
        assert response.status_code == 404
        assert "Teacher profile not found" in response.json()["detail"]

    async def test_update_success(self, client, override_auth, mock_teacher_db):
        override_auth(role="TEACHER")
        fake_teacher = make_fake_teacher()
        mock_teacher_db["get_teacher_by_user_id"].return_value = fake_teacher
        
        updated_teacher = make_fake_teacher({"experience": 8})
        mock_teacher_db["update_teacher"].return_value = updated_teacher

        response = await client.put("/api/v1/teachers/me", json={"experience": 8})
        assert response.status_code == 200
        data = response.json()
        assert data["experience"] == 8

    async def test_update_not_found(self, client, override_auth, mock_teacher_db):
        override_auth(role="TEACHER")
        mock_teacher_db["get_teacher_by_user_id"].return_value = None

        response = await client.put("/api/v1/teachers/me", json={"experience": 8})
        assert response.status_code == 404
        assert "Teacher profile not found" in response.json()["detail"]

    async def test_join_school_success(self, client, override_auth, mock_teacher_db):
        override_auth(role="TEACHER")
        fake_teacher = make_fake_teacher({"schoolId": "clxfake_school_001"})
        mock_teacher_db["join_school"].return_value = fake_teacher

        response = await client.post("/api/v1/teachers/me/join-school", json={"schoolId": "clxfake_school_001"})
        assert response.status_code == 200

    async def test_join_school_no_teacher(self, client, override_auth, mock_teacher_db):
        override_auth(role="TEACHER")
        mock_teacher_db["join_school"].return_value = None

        response = await client.post("/api/v1/teachers/me/join-school", json={"schoolId": "clxfake_school_001"})
        assert response.status_code == 404
        assert "Teacher profile not found" in response.json()["detail"]

    async def test_join_school_school_not_found(self, client, override_auth, mock_teacher_db):
        override_auth(role="TEACHER")
        mock_teacher_db["join_school"].return_value = False

        response = await client.post("/api/v1/teachers/me/join-school", json={"schoolId": "clxfake_school_999"})
        assert response.status_code == 404
        assert "School not found" in response.json()["detail"]

    async def test_get_qualifications(self, client, mock_teacher_db):
        mock_teacher_db["get_all_qualifications"].return_value = ["BACHELORS", "MASTERS", "PHD"]
        response = await client.get("/api/v1/teachers/qualifications")
        assert response.status_code == 200
        assert response.json() == ["BACHELORS", "MASTERS", "PHD"]

    async def test_get_subjects(self, client, mock_teacher_db):
        mock_teacher_db["get_all_subjects"].return_value = ["MATHS", "SCIENCE"]
        response = await client.get("/api/v1/teachers/subjects")
        assert response.status_code == 200
        assert response.json() == ["MATHS", "SCIENCE"]

    async def test_get_by_id_success(self, client, override_auth, mock_teacher_db):
        override_auth(role="STUDENT")
        fake_teacher = make_fake_teacher()
        mock_teacher_db["crud_get_teacher_by_id"].return_value = fake_teacher

        response = await client.get(f"/api/v1/teachers/{fake_teacher.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == fake_teacher.id

    async def test_get_by_id_not_found(self, client, override_auth, mock_teacher_db):
        override_auth(role="STUDENT")
        mock_teacher_db["crud_get_teacher_by_id"].return_value = None

        response = await client.get("/api/v1/teachers/clxfake_teacher_999")
        assert response.status_code == 404
        assert "Teacher not found" in response.json()["detail"]
