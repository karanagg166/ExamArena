# backend/tests/school/test_school.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from tests.dummy_data.schools import make_fake_school
from tests.dummy_data.teachers import make_fake_teacher, make_fake_principal

@pytest.mark.asyncio
class TestSchoolsApi:

    async def test_get_my_school_success(self, client, override_auth, mock_school_db):
        override_auth(role="PRINCIPAL")
        fake_school = make_fake_school()
        mock_school_db["get_school_by_user_id"].return_value = fake_school

        response = await client.get("/api/v1/schools/me")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == fake_school.id
        assert data["schoolCode"] == fake_school.schoolCode
        assert "phoneNo" not in data

    async def test_get_my_school_not_found(self, client, override_auth, mock_school_db):
        override_auth(role="PRINCIPAL")
        mock_school_db["get_school_by_user_id"].return_value = None

        response = await client.get("/api/v1/schools/me")
        assert response.status_code == 404
        assert "School profile not found" in response.json()["detail"]

    async def test_create_school_success(self, client, override_auth, mock_school_db):
        user = override_auth(role="PRINCIPAL")
        mock_school_db["get_school_by_user_id"].return_value = None
        fake_school = make_fake_school()
        mock_school_db["create_school"].return_value = fake_school

        # Set up teacher and principal checks for linking logic
        fake_teacher = make_fake_teacher()
        mock_school_db["get_teacher_by_user_id"].return_value = fake_teacher
        mock_school_db["get_principal_by_teacher_id"].return_value = None
        mock_school_db["create_principal"].return_value = make_fake_principal()
        
        # Mock teacher update in DB
        mock_update = AsyncMock()
        mock_school_db["db"].prisma.teacher.update = mock_update

        payload = {
            "name": "Test School",
            "address": "123 Test St",
            "city": "Mumbai",
            "state": "Maharashtra",
            "country": "India",
            "pincode": "400001",
            "schoolCode": "TST001",
            "type": "PUBLIC",
            "email": "school@test.dev",
            "website": "https://test.school"
        }
        response = await client.post("/api/v1/schools", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == fake_school.id
        mock_update.assert_called_once()

    async def test_create_school_already_manages(self, client, override_auth, mock_school_db):
        override_auth(role="PRINCIPAL")
        mock_school_db["get_school_by_user_id"].return_value = make_fake_school()

        payload = {
            "name": "Test School",
            "address": "123 Test St",
            "city": "Mumbai",
            "state": "Maharashtra",
            "country": "India",
            "pincode": "400001",
            "schoolCode": "TST001"
        }
        response = await client.post("/api/v1/schools", json=payload)
        assert response.status_code == 400
        assert "already manages a school" in response.json()["detail"]

    async def test_create_school_missing_fields(self, client, override_auth, mock_school_db):
        override_auth(role="PRINCIPAL")
        # schoolCode is required (omit it)
        payload = {
            "name": "Test School",
            "address": "123 Test St",
            "city": "Mumbai"
        }
        response = await client.post("/api/v1/schools", json=payload)
        assert response.status_code == 422

    async def test_get_profile_delegates_to_me(self, client, override_auth, mock_school_db):
        override_auth(role="PRINCIPAL")
        fake_school = make_fake_school()
        mock_school_db["get_school_by_user_id"].return_value = fake_school

        response = await client.get("/api/v1/schools/profile")
        assert response.status_code == 200
        assert response.json()["id"] == fake_school.id

    async def test_update_profile_success(self, client, override_auth, mock_school_db):
        override_auth(role="PRINCIPAL")
        fake_school = make_fake_school()
        mock_school_db["get_school_by_user_id"].return_value = fake_school
        
        updated_school = make_fake_school({"name": "Updated School"})
        mock_school_db["update_school"].return_value = updated_school

        response = await client.patch("/api/v1/schools/profile", json={"name": "Updated School"})
        assert response.status_code == 200
        assert response.json()["name"] == "Updated School"

    async def test_update_profile_crud_returns_none(self, client, override_auth, mock_school_db):
        override_auth(role="PRINCIPAL")
        fake_school = make_fake_school()
        mock_school_db["get_school_by_user_id"].return_value = fake_school
        mock_school_db["update_school"].return_value = None

        response = await client.patch("/api/v1/schools/profile", json={"name": "Updated School"})
        assert response.status_code == 500
        assert "Failed to update school" in response.json()["detail"]

    async def test_delete_profile_success(self, client, override_auth, mock_school_db):
        override_auth(role="PRINCIPAL")
        fake_school = make_fake_school()
        mock_school_db["get_school_by_user_id"].return_value = fake_school

        response = await client.delete("/api/v1/schools/profile")
        assert response.status_code == 204
        mock_school_db["delete_school"].assert_called_once_with(fake_school.id)

    async def test_fetch_schools_success(self, client, override_auth, mock_school_db):
        override_auth(role="STUDENT")
        fake_school = make_fake_school()
        mock_school_db["get_schools"].return_value = [fake_school]

        response = await client.get("/api/v1/schools")
        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_search_found(self, client, override_auth, mock_school_db):
        override_auth(role="STUDENT")
        fake_school = make_fake_school()
        mock_school_db["get_school_by_name"].return_value = fake_school

        response = await client.get("/api/v1/schools/search?name=Test School")
        assert response.status_code == 200
        assert response.json()["id"] == fake_school.id

    async def test_search_not_found(self, client, override_auth, mock_school_db):
        override_auth(role="STUDENT")
        mock_school_db["get_school_by_name"].return_value = None

        response = await client.get("/api/v1/schools/search?name=Unknown")
        assert response.status_code == 404

    async def test_by_code_found(self, client, override_auth, mock_school_db):
        override_auth(role="STUDENT")
        fake_school = make_fake_school()
        mock_school_db["get_school_by_code"].return_value = fake_school

        response = await client.get(f"/api/v1/schools/code/{fake_school.schoolCode}")
        assert response.status_code == 200
        assert response.json()["id"] == fake_school.id

    async def test_by_code_not_found(self, client, override_auth, mock_school_db):
        override_auth(role="STUDENT")
        mock_school_db["get_school_by_code"].return_value = None

        response = await client.get("/api/v1/schools/code/BADCODE")
        assert response.status_code == 404

    async def test_by_id_found(self, client, override_auth, mock_school_db):
        override_auth(role="STUDENT")
        fake_school = make_fake_school()
        mock_school_db["get_school_by_id"].return_value = fake_school

        response = await client.get(f"/api/v1/schools/{fake_school.id}")
        assert response.status_code == 200
        assert response.json()["id"] == fake_school.id

    async def test_by_id_not_found(self, client, override_auth, mock_school_db):
        override_auth(role="STUDENT")
        mock_school_db["get_school_by_id"].return_value = None

        response = await client.get("/api/v1/schools/clxfake_school_999")
        assert response.status_code == 404

    async def test_classes_for_school_success(self, client, override_auth, mock_school_db):
        override_auth(role="STUDENT")
        fake_school = make_fake_school()
        mock_school_db["get_school_by_id"].return_value = fake_school
        mock_school_db["get_school_classes_by_school_id"].return_value = [{"id": "class_1", "name": "12th-A"}]

        response = await client.get(f"/api/v1/schools/{fake_school.id}/classes")
        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_classes_for_school_not_found(self, client, override_auth, mock_school_db):
        override_auth(role="STUDENT")
        mock_school_db["get_school_by_id"].return_value = None

        response = await client.get("/api/v1/schools/clxfake_school_999/classes")
        assert response.status_code == 404
