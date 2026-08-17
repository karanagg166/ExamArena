import pytest

from app.school.schemas import SchoolResponse, SchoolType

TEST_SCHOOL_DATA = {
    "name": "Delhi Public School",
    "address": "123 Ring Road",
    "city": "New Delhi",
    "state": "Delhi",
    "country": "India",
    "pincode": "110001",
    "schoolCode": "DPS-DEL-01",
    "type": "PUBLIC",
    "email": "dps@school.edu",
    "website": "https://dps.edu",
}


class TestSchoolAPIEndpoints:
    """A14-A20: API tests for /api/v1/schools/* endpoints."""

    @pytest.mark.asyncio
    async def test_teacher_cannot_create_school_403(self, client, override_auth):
        override_auth(role="TEACHER")
        res = await client.post("/api/v1/schools", json=TEST_SCHOOL_DATA)
        assert res.status_code == 403
        assert "Only principals or admins" in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_student_cannot_create_school_403(self, client, override_auth):
        override_auth(role="STUDENT")
        res = await client.post("/api/v1/schools", json=TEST_SCHOOL_DATA)
        assert res.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_create_school_401(self, client):
        res = await client.post("/api/v1/schools", json=TEST_SCHOOL_DATA)
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_get_my_school_unauthenticated_returns_401(self, client):
        res = await client.get("/api/v1/schools/my-school")
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_fetch_schools_public_list(self, client, monkeypatch):
        async def mock_get_schools(filters):
            return []

        monkeypatch.setattr("app.school.crud.get_schools", mock_get_schools)

        res = await client.get("/api/v1/schools")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
