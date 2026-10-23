import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from app.main import app


@pytest.mark.asyncio
async def test_health_liveness_endpoint():
    """Verify liveness probe returns 200 with service metadata and git_commit."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for path in ["/health", "/health/live", "/ready", "/api/health", "/api/health/live", "/api/ready"]:
            resp = await client.get(path)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"
            assert data["service"] == "exam-arena-api"
            assert "git_commit" in data


@pytest.mark.asyncio
async def test_health_readiness_connected():
    """Verify readiness returns 200 when database and redis are healthy."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("app.core.redis.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.ping.return_value = True
            mock_get_redis.return_value = mock_redis

            resp = await client.get("/health/ready")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ready"
            assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_health_readiness_fails_when_db_down():
    """Verify readiness returns 503 when database is unreachable."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("app.core.database.get_session") as mock_session_ctx:
            mock_session_ctx.side_effect = Exception("DB connection timeout")

            resp = await client.get("/health/ready")
            assert resp.status_code == 503
            data = resp.json()
            assert data["status"] == "unready"
            assert data["database"] == "disconnected"
            assert "DB connection timeout" in data["errors"][0]
