import pytest


class TestExamsAPIEndpoints:
    """A44-A54: API tests for /api/v1/exams/* endpoints."""

    @pytest.mark.asyncio
    async def test_student_cannot_create_exam_403(self, client, override_auth):
        override_auth(role="STUDENT")
        res = await client.post(
            "/api/v1/exams",
            json={
                "name": "Test Exam",
                "description": "Desc",
                "scheduledAt": "2026-09-01T00:00:00Z",
                "duration": 60,
                "maxMarks": 100,
                "type": "QUIZ",
            },
        )
        assert res.status_code == 403
        assert "Only teachers" in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_create_exam_401(self, client):
        res = await client.post(
            "/api/v1/exams",
            json={
                "name": "Test Exam",
                "description": "Desc",
                "scheduledAt": "2026-09-01T00:00:00Z",
                "duration": 60,
                "maxMarks": 100,
                "type": "QUIZ",
            },
        )
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_public_exams_list_accessible(
        self, client, override_auth, monkeypatch
    ):
        override_auth(role="STUDENT")

        async def mock_get_published_exams(**kwargs):
            return []

        monkeypatch.setattr(
            "app.exams.crud.get_published_exams", mock_get_published_exams
        )

        res = await client.get("/api/v1/exams/public")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    @pytest.mark.asyncio
    async def test_student_exams_forbidden_for_teacher(self, client, override_auth):
        override_auth(role="TEACHER")
        res = await client.get("/api/v1/exams/student")
        assert res.status_code == 403
        assert "Only students" in res.json()["detail"]
