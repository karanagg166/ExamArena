"""Integration tests for audit trail persistence, request correlation, and audit querying."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.actions import AuditAction, AuditResourceType
from app.core.models import AuditLog, Role
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_audit_log_persisted_on_signup_and_login(
    client: AsyncClient, db_session: AsyncSession
):
    """Verify signup, login, and logout actions generate persistent audit log entries."""
    email = "audit.user@test.examarena.dev"
    reg_payload = {
        "name": "Audit Tester",
        "email": email,
        "password": "Password123!",
        "role": "STUDENT",
        "phoneNo": "9988776655",
        "dateOfBirth": "2000-01-01T00:00:00Z",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "pincode": "560001",
    }

    # 1. Signup
    reg_resp = await client.post("/api/v1/auth/signup", json=reg_payload)
    assert reg_resp.status_code == 200
    user_id = reg_resp.json()["id"]

    # Verify signup audit log
    await db_session.commit()
    stmt = (
        select(AuditLog)
        .where(AuditLog.action == AuditAction.AUTH_SIGNUP.value)
        .order_by(AuditLog.timestamp.desc())
    )
    res = await db_session.execute(stmt)
    signup_log = res.scalar_one_or_none()
    assert signup_log is not None
    assert signup_log.actorEmail == email
    assert signup_log.actorId == user_id
    assert signup_log.resourceType == AuditResourceType.USER.value
    assert signup_log.status == "SUCCESS"
    assert signup_log.requestId is not None

    # 2. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert login_resp.status_code == 200

    # Verify login audit log
    await db_session.commit()
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.action == AuditAction.AUTH_LOGIN_SUCCESS.value,
            AuditLog.actorEmail == email,
        )
        .order_by(AuditLog.timestamp.desc())
    )
    res = await db_session.execute(stmt)
    login_log = res.scalar_one_or_none()
    assert login_log is not None
    assert login_log.actorId == user_id
    assert login_log.status == "SUCCESS"

    # 3. Logout
    logout_resp = await client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 200

    await db_session.commit()
    stmt = (
        select(AuditLog)
        .where(AuditLog.action == AuditAction.AUTH_LOGOUT.value)
        .order_by(AuditLog.timestamp.desc())
    )
    res = await db_session.execute(stmt)
    logout_log = res.scalar_one_or_none()
    assert logout_log is not None
    assert logout_log.status == "SUCCESS"


@pytest.mark.asyncio
async def test_audit_log_on_failed_login(
    client: AsyncClient, db_session: AsyncSession
):
    """Verify failed login attempts generate audit logs with failure status."""
    # Attempt login with non-existent email
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@test.examarena.dev", "password": "WrongPassword!"},
    )
    assert resp.status_code == 400

    await db_session.commit()
    stmt = (
        select(AuditLog)
        .where(AuditLog.action == AuditAction.AUTH_LOGIN_FAILED.value)
        .order_by(AuditLog.timestamp.desc())
    )
    res = await db_session.execute(stmt)
    failed_log = res.scalar_one_or_none()
    assert failed_log is not None
    assert failed_log.status == "FAILURE"
    assert failed_log.metadata_ is not None
    assert failed_log.metadata_.get("reason") == "INVALID_EMAIL"


@pytest.mark.asyncio
async def test_audit_logs_query_endpoint_rbac(
    auth_client_factory, db_session: AsyncSession
):
    """Verify GET /api/v1/audit/logs requires ADMIN or PRINCIPAL role and supports filtering."""
    # 1. Create student user and attempt to fetch audit logs -> 403
    student = await create_user_factory(db_session, role=Role.STUDENT)
    await db_session.commit()

    student_client = await auth_client_factory(student)
    forbidden_resp = await student_client.get("/api/v1/audit/logs")
    assert forbidden_resp.status_code == 403

    # 2. Record an audit log event and verify admin can query it -> 200
    from app.audit.service import record_audit_event
    await record_audit_event(
        action=AuditAction.SCHOOL_CREATED,
        resource_type=AuditResourceType.SCHOOL,
        resource_id="test-school-1",
        actor_id=student.id,
        actor_email=student.email,
        actor_role=student.role,
        status="SUCCESS",
        metadata={"name": "Test Academy"},
    )

    admin = await create_user_factory(db_session, role=Role.ADMIN)
    await db_session.commit()

    admin_client = await auth_client_factory(admin)
    allowed_resp = await admin_client.get("/api/v1/audit/logs?limit=10")
    assert allowed_resp.status_code == 200
    logs = allowed_resp.json()
    assert isinstance(logs, list)
    assert len(logs) > 0
    assert logs[0]["action"] == AuditAction.SCHOOL_CREATED
    assert logs[0]["resourceType"] == AuditResourceType.SCHOOL
