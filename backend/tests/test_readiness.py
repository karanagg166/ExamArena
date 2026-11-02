from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_db_infrastructure():
    """Bypass real local PostgreSQL startup for pure mock readiness tests."""
    yield


@pytest.mark.asyncio
async def test_health_liveness_returns_ok():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "exam-arena-api"


@pytest.mark.asyncio
async def test_health_ready_success_contract():
    with patch("app.core.database.get_session") as mock_get_session, \
         patch("app.core.redis.get_redis") as mock_get_redis:
        mock_session = AsyncMock()
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        mock_get_redis.return_value = mock_redis

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
            assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_health_ready_database_timeout_returns_503():
    with patch("app.core.database.get_session") as mock_get_session:
        mock_get_session.side_effect = TimeoutError("Timed out")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unready"
            assert data["database"] == "disconnected"
            assert "errors" in data
            assert "DATABASE_TIMEOUT" in data["errors"]


@pytest.mark.asyncio
async def test_health_ready_raw_database_error_is_redacted():
    with patch("app.core.database.get_session") as mock_get_session:
        mock_get_session.side_effect = Exception("password authentication failed for user 'neondb_owner' at ep-steep-glade.neon.tech")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unready"
            assert data["database"] == "disconnected"
            assert data["errors"] == ["DATABASE_UNAVAILABLE"]
            assert data["request_id"] is not None
            # Verify no credentials or internal host leaked in payload
            assert "neondb_owner" not in str(data)
            assert "ep-steep-glade.neon.tech" not in str(data)


@pytest.mark.asyncio
async def test_ready_alias_points_to_health_ready():
    with patch("app.core.database.get_session") as mock_get_session, \
         patch("app.core.redis.get_redis") as mock_get_redis:
        mock_session = AsyncMock()
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        mock_get_redis.return_value = mock_redis

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
            assert data["database"] == "connected"
