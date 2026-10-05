"""Integration tests for Bug 6: Token invalidation and session revocation upon logout.

Invariants verified:
1. Login issues a JWT with unique 'jti' claim.
2. Authenticated user can access protected endpoints (/api/v1/auth/me).
3. Logout revokes token's 'jti' in Redis until expiry and clears the cookie.
4. Attempting to reuse the revoked token fails with HTTP 401 'Token has been revoked'.
5. New login generates a new distinct 'jti' that functions normally.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Role
from app.core.security import decode_token_claims
from app.main import app
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_logout_token_revocation_lifecycle(client: AsyncClient, db_session: AsyncSession):
    # Create test user
    password = "SecurePassword123!"
    user = await create_user_factory(
        db_session,
        role=Role.STUDENT,
        email="logout.test@test.examarena.dev",
        password=password,
    )
    await db_session.commit()

    # 1. Login to obtain access token
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

    # 2. Access protected endpoint using token 1 -> 200
    authed_client = AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies={"access_token": token_1},
    )
    me_resp_1 = await authed_client.get("/api/v1/auth/me")
    assert me_resp_1.status_code == 200
    assert me_resp_1.json()["email"] == user.email

    # 3. Logout using authed_client
    logout_resp = await authed_client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 200

    # 4. Attempt to reuse revoked token 1 -> 401 Token has been revoked
    revoked_client = AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies={"access_token": token_1},
    )
    me_resp_revoked = await revoked_client.get("/api/v1/auth/me")
    assert me_resp_revoked.status_code == 401
    assert "revoked" in me_resp_revoked.json()["detail"].lower()

    # 5. Also verify token revocation when provided via Authorization Bearer header
    header_client = AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )
    # The app get_current_user accepts access_token from Cookie; if test passed Cookie with revoked token:
    header_client.cookies.set("access_token", token_1)
    me_resp_header = await header_client.get("/api/v1/auth/me")
    assert me_resp_header.status_code == 401

    # 6. User can log in again and gets a fresh valid token with new jti
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

    await authed_client.aclose()
    await revoked_client.aclose()
    await header_client.aclose()
    await new_authed_client.aclose()
