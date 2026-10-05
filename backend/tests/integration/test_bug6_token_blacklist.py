"""Integration tests for Bug 6: Token invalidation, fail-closed revocation, and cookie lifecycle upon logout.

Invariants verified:
1. Login issues a JWT with unique 'jti' claim and sets the access_token HTTP-only cookie.
2. Protected endpoints (/api/v1/auth/me) require cookie authentication.
3. Logout revokes token's 'jti' in Redis and clears/expires the access_token cookie in the response.
4. Attempting to reuse the revoked token returns HTTP 401 'Token has been revoked'.
5. Logout endpoint accepts token via Authorization: Bearer header for explicit revocation.
6. Fail-closed: If Redis is unavailable during a protected request, returns HTTP 503 rather than failing open.
7. Fail-closed: If Redis is unavailable during logout, returns HTTP 503 rather than falsely claiming guaranteed revocation.
8. Blacklist TTL corresponds to the remaining lifetime of the token.
9. Fresh login generates a new distinct 'jti' that functions normally when Redis is healthy.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.token_blacklist import TokenBlacklistUnavailableError, blacklist_token
from app.core.config import settings
from app.core.models import Role
from app.core.security import create_access_token, decode_token_claims
from app.main import app
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_logout_token_revocation_and_cookie_lifecycle(
    client: AsyncClient, db_session: AsyncSession
):
    """Verify login sets cookie, logout clears cookie and revokes JTI, and reuse returns 401."""
    password = "SecurePassword123!"
    user = await create_user_factory(
        db_session,
        role=Role.STUDENT,
        email="logout.cookie@test.examarena.dev",
        password=password,
    )
    await db_session.commit()

    # 1. Login to obtain access token cookie
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )
    assert login_resp.status_code == 200
    token_1 = login_resp.cookies.get("access_token")
    assert token_1 is not None

    claims_1 = decode_token_claims(token_1)
    assert claims_1 is not None
    assert "jti" in claims_1
    jti_1 = claims_1["jti"]

    # 2. Access protected endpoint using the logged-in client -> 200
    me_resp_1 = await client.get("/api/v1/auth/me")
    assert me_resp_1.status_code == 200
    assert me_resp_1.json()["email"] == user.email

    # 3. Logout using client
    logout_resp = await client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 200
    assert logout_resp.json()["message"] == "Logged out successfully"

    # Verify response Set-Cookie header deletes / expires the access_token cookie
    set_cookie = logout_resp.headers.get("set-cookie", "")
    assert "access_token" in set_cookie
    assert "max-age=0" in set_cookie.lower() or "expires=" in set_cookie.lower()

    # 4. Attempting request with client after logout (cookie cleared by response) -> 401 Not authenticated
    me_after_logout = await client.get("/api/v1/auth/me")
    assert me_after_logout.status_code == 401
    assert "not authenticated" in me_after_logout.json()["detail"].lower()

    # 5. Attacker attempting to replay the old token_1 via explicit cookie -> 401 Token has been revoked
    revoked_client = AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies={"access_token": token_1},
    )
    me_resp_revoked = await revoked_client.get("/api/v1/auth/me")
    assert me_resp_revoked.status_code == 401
    assert "revoked" in me_resp_revoked.json()["detail"].lower()

    # 6. Fresh login generates distinct JTI that authenticates cleanly
    login_resp_2 = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )
    assert login_resp_2.status_code == 200
    token_2 = login_resp_2.cookies.get("access_token")
    assert token_2 is not None
    assert token_2 != token_1

    claims_2 = decode_token_claims(token_2)
    assert claims_2["jti"] != jti_1

    new_authed_client = AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies={"access_token": token_2},
    )
    me_resp_2 = await new_authed_client.get("/api/v1/auth/me")
    assert me_resp_2.status_code == 200
    assert me_resp_2.json()["email"] == user.email

    await revoked_client.aclose()
    await new_authed_client.aclose()


@pytest.mark.asyncio
async def test_logout_accepts_bearer_token_while_protected_routes_remain_cookie_only(
    client: AsyncClient, db_session: AsyncSession
):
    """Verify logout accepts token via Authorization: Bearer header,

    while protected API endpoints strictly require the HTTP-only cookie.
    """
    password = "SecurePassword123!"
    user = await create_user_factory(
        db_session,
        role=Role.STUDENT,
        email="logout.bearer@test.examarena.dev",
        password=password,
    )
    await db_session.commit()

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )
    token = login_resp.cookies.get("access_token")
    assert token is not None

    # Protected endpoint (/api/v1/auth/me) with ONLY Bearer header returns 401 (cookie-only policy)
    bearer_client = AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )
    resp_bearer_auth = await bearer_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_bearer_auth.status_code == 401
    assert "not authenticated" in resp_bearer_auth.json()["detail"].lower()

    # Logout endpoint DOES accept token via Authorization: Bearer header
    logout_bearer_resp = await bearer_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_bearer_resp.status_code == 200

    # Token is now revoked: presenting it as cookie fails with 401 'Token has been revoked'
    cookie_client = AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies={"access_token": token},
    )
    resp_revoked = await cookie_client.get("/api/v1/auth/me")
    assert resp_revoked.status_code == 401
    assert "revoked" in resp_revoked.json()["detail"].lower()

    await bearer_client.aclose()
    await cookie_client.aclose()


@pytest.mark.asyncio
async def test_redis_unavailable_fail_closed_behavior(
    client: AsyncClient, db_session: AsyncSession
):
    """Verify that when the Redis blacklist service is unreachable:

    1. Protected requests fail closed with 503 Service Unavailable (not 200).
    2. Logout requests fail closed with 503 Service Unavailable (do not report false success).
    3. Requests succeed again once Redis is restored.
    """
    password = "SecurePassword123!"
    user = await create_user_factory(
        db_session,
        role=Role.STUDENT,
        email="redis.failclosed@test.examarena.dev",
        password=password,
    )
    await db_session.commit()

    # 1. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )
    token = login_resp.cookies.get("access_token")
    assert token is not None

    authed_client = AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies={"access_token": token},
    )

    # 2. Redis available -> request succeeds (200)
    resp_healthy = await authed_client.get("/api/v1/auth/me")
    assert resp_healthy.status_code == 200

    # 3. Simulate Redis failure during protected request:
    # Patch get_redis to raise an error when checking blacklist
    with patch(
        "app.auth.token_blacklist.get_redis",
        side_effect=Exception("Redis connection refused"),
    ):
        resp_redis_down = await authed_client.get("/api/v1/auth/me")
        # Must FAIL CLOSED with 503, never silently authenticate
        assert resp_redis_down.status_code == 503
        assert (
            resp_redis_down.json()["detail"]
            == "Authentication service temporarily unavailable"
        )

    # 4. Simulate Redis failure during logout:
    with patch(
        "app.auth.token_blacklist.get_redis",
        side_effect=Exception("Redis connection refused"),
    ):
        logout_redis_down = await authed_client.post("/api/v1/auth/logout")
        # Must FAIL with 503 rather than claiming guaranteed revocation
        assert logout_redis_down.status_code == 503
        assert (
            logout_redis_down.json()["detail"]
            == "Authentication service temporarily unavailable"
        )

    # 5. Redis restored: protected request succeeds again
    resp_restored = await authed_client.get("/api/v1/auth/me")
    assert resp_restored.status_code == 200
    assert resp_restored.json()["email"] == user.email

    await authed_client.aclose()


@pytest.mark.asyncio
async def test_blacklist_ttl_matches_remaining_token_lifetime():
    """Verify blacklist TTL passed to Redis matches remaining JWT expiration time."""
    mock_redis = AsyncMock()
    mock_redis.setex = AsyncMock()

    with patch("app.auth.token_blacklist.get_redis", return_value=mock_redis):
        # 1. Direct call to blacklist_token with 1800 seconds
        await blacklist_token("test-jti-123", 1800)
        mock_redis.setex.assert_awaited_once_with(
            "blacklist:jti:test-jti-123", 1800, "1"
        )

    # 2. End-to-end logout TTL verification
    mock_redis_logout = AsyncMock()
    mock_redis_logout.setex = AsyncMock()

    user_id = "usr_ttl_test"
    # Create token expiring in 15 minutes
    token = create_access_token(user_id)
    claims = decode_token_claims(token)
    assert claims is not None
    jti = claims["jti"]

    authed_client = AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies={"access_token": token},
    )

    with patch(
        "app.auth.token_blacklist.get_redis", return_value=mock_redis_logout
    ):
        logout_resp = await authed_client.post("/api/v1/auth/logout")
        assert logout_resp.status_code == 200

        mock_redis_logout.setex.assert_awaited_once()
        call_args = mock_redis_logout.setex.call_args[0]
        # (key, ttl, value)
        assert call_args[0] == f"blacklist:jti:{jti}"
        ttl = call_args[1]
        # Remaining time should be approximately ACCESS_TOKEN_EXPIRE_MINUTES * 60 (within 10s)
        expected_ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        assert abs(ttl - expected_ttl) < 10
        assert call_args[2] == "1"

    await authed_client.aclose()
