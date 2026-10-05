from datetime import UTC, datetime, timedelta
import pytest
from httpx import AsyncClient
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.models import Role, User
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_user_registration_and_login_flow(
    client: AsyncClient, db_session: AsyncSession
):
    """Test full registration and login flow for a student."""
    reg_payload = {
        "name": "Alex Mercer",
        "email": "alex.mercer@test.examarena.dev",
        "password": "SecurePassword123!",
        "role": "STUDENT",
        "phoneNo": "9876543210",
        "dateOfBirth": "2002-05-15T00:00:00Z",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "pincode": "560001",
    }

    # 1. Register (signup)
    reg_resp = await client.post("/api/v1/auth/signup", json=reg_payload)
    assert reg_resp.status_code == 200
    reg_data = reg_resp.json()
    assert reg_data["email"] == "alex.mercer@test.examarena.dev"
    assert reg_data["role"] == "STUDENT"
    assert "password" not in reg_data

    # Verify user exists in database
    result = await db_session.execute(
        select(User).where(User.email == "alex.mercer@test.examarena.dev")
    )
    db_user = result.scalar_one_or_none()
    assert db_user is not None
    assert db_user.name == "Alex Mercer"

    # 2. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "alex.mercer@test.examarena.dev",
            "password": "SecurePassword123!",
        },
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.cookies


@pytest.mark.asyncio
async def test_duplicate_email_registration_rejected(
    client: AsyncClient, db_session: AsyncSession
):
    """Verify system blocks registering duplicate emails with 400 Bad Request."""
    await create_user_factory(
        db_session,
        email="duplicate@test.examarena.dev",
        password="Password123!",
    )
    await db_session.commit()

    reg_payload = {
        "name": "Second User",
        "email": "duplicate@test.examarena.dev",
        "password": "OtherPassword123!",
        "role": "STUDENT",
        "phoneNo": "9123456789",
        "dateOfBirth": "2000-01-01T00:00:00Z",
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "pincode": "400001",
    }

    reg_resp = await client.post("/api/v1/auth/signup", json=reg_payload)
    assert reg_resp.status_code == 400
    assert "already registered" in reg_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_invalid_password_returns_400(
    client: AsyncClient, db_session: AsyncSession
):
    """Verify invalid credentials return 400 Bad Request."""
    await create_user_factory(
        db_session,
        email="user.login@test.examarena.dev",
        password="CorrectPassword123!",
    )
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "user.login@test.examarena.dev",
            "password": "WrongPassword!",
        },
    )
    assert resp.status_code == 401
    assert "invalid email or password" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_enumeration_resistance(
    client: AsyncClient, db_session: AsyncSession
):
    """Bug 5: Verify login does not disclose whether email exists by returning identical status and payload."""
    await create_user_factory(
        db_session,
        email="realuser@test.examarena.dev",
        password="RealPassword123!",
    )
    await db_session.commit()

    resp_nonexistent = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "definitely.not.registered@test.examarena.dev",
            "password": "AnyPassword123!",
        },
    )

    resp_wrong_password = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "realuser@test.examarena.dev",
            "password": "WrongPassword123!",
        },
    )

    assert resp_nonexistent.status_code == 401
    assert resp_wrong_password.status_code == 401
    assert resp_nonexistent.status_code == resp_wrong_password.status_code
    assert resp_nonexistent.json() == resp_wrong_password.json()
    assert resp_nonexistent.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_authenticated_me_endpoint(
    client: AsyncClient,
    auth_client_factory,
    db_session: AsyncSession,
):
    """Verify /api/v1/auth/me returns current user info."""
    user = await create_user_factory(
        db_session,
        name="Samantha Jones",
        email="samantha@test.examarena.dev",
        role=Role.TEACHER,
    )
    await db_session.commit()

    auth_client = await auth_client_factory(user)
    me_resp = await auth_client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["id"] == user.id
    assert data["email"] == "samantha@test.examarena.dev"
    assert data["role"] == "TEACHER"


@pytest.mark.asyncio
async def test_tampered_or_invalid_token_rejected(client: AsyncClient):
    """Verify tampered JWT tokens return 401 Unauthorized."""
    client.cookies.set("access_token", "invalid.tampered.token")
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_password_change_flow(
    auth_client_factory,
    db_session: AsyncSession,
):
    """Verify password change endpoint validates old password and updates hash."""
    user = await create_user_factory(
        db_session,
        email="changepwd@test.examarena.dev",
        password="OldPassword123!",
    )
    await db_session.commit()

    auth_client = await auth_client_factory(user)

    # 1. Invalid old password
    fail_resp = await auth_client.post(
        "/api/v1/auth/change-password",
        json={
            "currentPassword": "IncorrectOldPassword",
            "newPassword": "NewSecurePassword123!",
        },
    )
    assert fail_resp.status_code == 400

    # 2. Valid old password
    success_resp = await auth_client.post(
        "/api/v1/auth/change-password",
        json={
            "currentPassword": "OldPassword123!",
            "newPassword": "NewSecurePassword123!",
        },
    )
    assert success_resp.status_code == 200


@pytest.mark.asyncio
async def test_expired_token_rejected_returns_401(
    client: AsyncClient, db_session: AsyncSession
):
    """Verify expired JWT tokens return 401 Unauthorized."""
    user = await create_user_factory(
        db_session, email="expired.token@test.examarena.dev"
    )
    await db_session.commit()

    expired_time = datetime.now(UTC) - timedelta(minutes=15)
    payload = {"sub": str(user.id), "exp": expired_time, "jti": "expired-jti-uuid"}
    expired_token = jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    client.cookies.set("access_token", expired_token)
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "invalid token" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_malformed_token_rejected_returns_401(
    client: AsyncClient, db_session: AsyncSession
):
    """Verify malformed or invalidly signed JWT returns 401 Unauthorized."""
    user = await create_user_factory(
        db_session, email="malformed.token@test.examarena.dev"
    )
    await db_session.commit()

    # Token signed with completely different secret key
    bad_token = jwt.encode(
        {"sub": str(user.id), "exp": datetime.now(UTC) + timedelta(hours=1)},
        "wrong-secret-key-123",
        algorithm=settings.ALGORITHM,
    )
    client.cookies.set("access_token", bad_token)
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "invalid token" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_legacy_token_without_jti_is_accepted(
    client: AsyncClient, db_session: AsyncSession
):
    """Verify backward compatibility: JWT tokens without 'jti' bypass blacklist checks and authenticate."""
    user = await create_user_factory(
        db_session, email="legacy.token@test.examarena.dev"
    )
    await db_session.commit()

    # Token created without 'jti' claim (legacy token)
    legacy_payload = {
        "sub": str(user.id),
        "exp": datetime.now(UTC) + timedelta(minutes=30),
    }
    legacy_token = jwt.encode(
        legacy_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    client.cookies.set("access_token", legacy_token)
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == user.id
    assert data["email"] == "legacy.token@test.examarena.dev"

