import pytest


class TestJoinRequestsAPIEndpoints:
    """A36-A43: API tests for /api/v1/join-requests/* endpoints."""

    @pytest.mark.asyncio
    async def test_teacher_cannot_join_class_by_code_403(self, client, override_auth):
        override_auth(role="TEACHER")
        res = await client.post(
            "/api/v1/join-requests/join-by-code", json={"joinCode": "CODE1234"}
        )
        assert res.status_code == 403
        assert "Only students" in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_student_invalid_join_code_404(
        self, client, override_auth, monkeypatch
    ):
        override_auth(role="STUDENT")

        async def mock_get_student(*args, **kwargs):
            return None

        async def mock_get_class_by_code(*args, **kwargs):
            return None

        monkeypatch.setattr(
            "app.join_requests.router.get_student_by_user_id", mock_get_student
        )
        monkeypatch.setattr(
            "app.join_requests.router.get_class_by_join_code", mock_get_class_by_code
        )

        res = await client.post(
            "/api/v1/join-requests/join-by-code", json={"joinCode": "NONEXISTENT"}
        )
        assert res.status_code == 404
        assert "Invalid or expired join code" in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_get_my_requests_401(self, client):
        res = await client.get("/api/v1/join-requests/me")
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_teacher_cannot_get_my_join_requests_403(self, client, override_auth):
        override_auth(role="TEACHER")
        res = await client.get("/api/v1/join-requests/me")
        assert res.status_code == 403
        assert "Only students" in res.json()["detail"]
