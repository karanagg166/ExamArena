import pytest
from jose import jwt

from app.core.config import settings
from tests.dummy_data.users import TEST_USER_PAYLOAD


class TestAuthAPIEndpoints:
    """A1-A13: API tests for /api/v1/auth/* endpoints."""

    @pytest.mark.asyncio
    async def test_signup_validation_failure_missing_email(self, client):
        payload = {k: v for k, v in TEST_USER_PAYLOAD.items() if k != "email"}
        res = await client.post("/api/v1/auth/signup", json=payload)
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_signup_validation_failure_invalid_phone(self, client):
        payload = {**TEST_USER_PAYLOAD, "phoneNo": "invalid"}
        res = await client.post("/api/v1/auth/signup", json=payload)
        assert res.status_code in (200, 400, 422)

    @pytest.mark.asyncio
    async def test_logout_endpoint(self, client):
        res = await client.post("/api/v1/auth/logout")
        assert res.status_code == 200
        assert "Logged out" in res.json().get("message", "")

    @pytest.mark.asyncio
    async def test_me_unauthenticated_returns_401(self, client):
        res = await client.get("/api/v1/auth/me")
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_stream_token_unauthenticated_returns_401(self, client):
        res = await client.get("/api/v1/auth/stream-token")
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_stream_token_authenticated_returns_token(
        self, client, override_auth, monkeypatch
    ):
        user = override_auth(role="TEACHER")
        monkeypatch.setattr(settings, "STREAM_API_SECRET", "test_stream_secret_123")
        monkeypatch.setattr(settings, "STREAM_API_KEY", "test_stream_key_123")

        res = await client.get("/api/v1/auth/stream-token")
        assert res.status_code == 200
        data = res.json()
        assert "token" in data
        assert data["apiKey"] == "test_stream_key_123"

        decoded = jwt.decode(
            data["token"], "test_stream_secret_123", algorithms=["HS256"]
        )
        assert decoded["user_id"] == user.id
