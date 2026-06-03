# backend/tests/principal/test_principal.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from tests.dummy_data.teachers import make_fake_teacher, make_fake_principal

@pytest.mark.asyncio
class TestPrincipalsApi:

    async def test_create_success(self, client, override_auth, mock_principal_db):
        override_auth(role="PRINCIPAL")
        fake_teacher = make_fake_teacher()
        mock_principal_db["get_teacher_by_user_id"].return_value = fake_teacher
        mock_principal_db["get_principal_by_teacher_id"].return_value = None
        
        # Mock db.prisma.teacher.update
        mock_update = AsyncMock(return_value=fake_teacher)
        mock_principal_db["db"].prisma.teacher.update = mock_update
        
        fake_principal = make_fake_principal()
        mock_principal_db["create_principal"].return_value = fake_principal

        payload = {
            "experience": 10,
            "schoolId": "clxfake_school_001",
        }
        response = await client.post("/api/v1/principals", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == fake_principal.id
        assert data["experience"] == 10
        mock_update.assert_called_once()

    async def test_create_no_teacher_profile(self, client, override_auth, mock_principal_db):
        override_auth(role="PRINCIPAL")
        mock_principal_db["get_teacher_by_user_id"].return_value = None

        payload = {
            "experience": 10,
            "schoolId": "clxfake_school_001",
        }
        response = await client.post("/api/v1/principals", json=payload)
        assert response.status_code == 404
        assert "Teacher profile not found" in response.json()["detail"]

    async def test_create_already_exists(self, client, override_auth, mock_principal_db):
        override_auth(role="PRINCIPAL")
        fake_teacher = make_fake_teacher()
        mock_principal_db["get_teacher_by_user_id"].return_value = fake_teacher
        mock_principal_db["get_principal_by_teacher_id"].return_value = make_fake_principal()

        payload = {
            "experience": 10,
            "schoolId": "clxfake_school_001",
        }
        response = await client.post("/api/v1/principals", json=payload)
        assert response.status_code == 409
        assert "Principal profile already exists" in response.json()["detail"]

    async def test_get_me_success(self, client, override_auth, mock_principal_db):
        override_auth(role="PRINCIPAL")
        fake_teacher = make_fake_teacher()
        mock_principal_db["get_teacher_by_user_id"].return_value = fake_teacher
        fake_principal = make_fake_principal()
        mock_principal_db["get_principal_by_teacher_id"].return_value = fake_principal

        response = await client.get("/api/v1/principals/me")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == fake_principal.id
        assert data["experience"] == fake_principal.experience

    async def test_get_me_no_teacher(self, client, override_auth, mock_principal_db):
        override_auth(role="PRINCIPAL")
        mock_principal_db["get_teacher_by_user_id"].return_value = None

        response = await client.get("/api/v1/principals/me")
        assert response.status_code == 404
        assert "Teacher profile not found" in response.json()["detail"]

    async def test_get_me_no_principal(self, client, override_auth, mock_principal_db):
        override_auth(role="PRINCIPAL")
        fake_teacher = make_fake_teacher()
        mock_principal_db["get_teacher_by_user_id"].return_value = fake_teacher
        mock_principal_db["get_principal_by_teacher_id"].return_value = None

        response = await client.get("/api/v1/principals/me")
        assert response.status_code == 404
        assert "Principal profile not found" in response.json()["detail"]

    async def test_update_success(self, client, override_auth, mock_principal_db):
        override_auth(role="PRINCIPAL")
        fake_teacher = make_fake_teacher()
        mock_principal_db["get_teacher_by_user_id"].return_value = fake_teacher
        
        fake_principal = make_fake_principal()
        mock_principal_db["get_principal_by_teacher_id"].return_value = fake_principal
        
        updated_principal = make_fake_principal({"experience": 15})
        mock_principal_db["update_principal"].return_value = updated_principal

        response = await client.put("/api/v1/principals/me", json={"experience": 15})
        assert response.status_code == 200
        data = response.json()
        assert data["experience"] == 15

    async def test_update_not_found(self, client, override_auth, mock_principal_db):
        override_auth(role="PRINCIPAL")
        fake_teacher = make_fake_teacher()
        mock_principal_db["get_teacher_by_user_id"].return_value = fake_teacher
        mock_principal_db["get_principal_by_teacher_id"].return_value = None

        response = await client.put("/api/v1/principals/me", json={"experience": 15})
        assert response.status_code == 404
        assert "Principal profile not found" in response.json()["detail"]
