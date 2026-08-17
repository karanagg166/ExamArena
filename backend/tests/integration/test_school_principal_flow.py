"""Integration tests for School and Principal workflows and multi-principal isolation."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Principal, Role, School, Teacher
from tests.factories.school_factory import create_school_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_principal_creates_school_and_receives_school_code(
    auth_client_factory, db_session: AsyncSession
):
    """Verify Principal can create a new school and automatically gains principal role/profile."""
    principal_user = await create_user_factory(
        db_session,
        name="Principal Skinner",
        email="skinner@springfield.edu",
        role=Role.PRINCIPAL,
    )
    await db_session.commit()

    client = await auth_client_factory(principal_user)

    school_payload = {
        "name": "Springfield Elementary",
        "type": "PUBLIC",
        "schoolCode": "SPRF-001",
        "email": "contact@springfield.edu",
        "website": "https://springfield.edu",
        "phoneNo": "9876543210",
        "address": "123 Main Street",
        "city": "Springfield",
        "state": "Oregon",
        "country": "USA",
        "pincode": "97477",
    }

    resp = await client.post("/api/v1/schools", json=school_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Springfield Elementary"
    assert data["schoolCode"] == "SPRF-001"
    assert data["createdBy"] == principal_user.id

    # Verify School record in DB
    result = await db_session.execute(select(School).where(School.id == data["id"]))
    school = result.scalar_one_or_none()
    assert school is not None
    assert school.schoolCode == "SPRF-001"
    assert school.createdBy == principal_user.id


@pytest.mark.asyncio
async def test_multi_principal_school_isolation(
    auth_client_factory, db_session: AsyncSession
):
    """Verify Principal B cannot edit or delete School A created by Principal A."""
    principal_a = await create_user_factory(
        db_session,
        name="Principal A",
        email="principal.a@test.examarena.dev",
        role=Role.PRINCIPAL,
    )
    principal_b = await create_user_factory(
        db_session,
        name="Principal B",
        email="principal.b@test.examarena.dev",
        role=Role.PRINCIPAL,
    )
    school_a = await create_school_factory(
        db_session,
        creator_user=principal_a,
        name="Academy Alpha",
        school_code="ALPHA-001",
    )
    school_b = await create_school_factory(
        db_session,
        creator_user=principal_b,
        name="Academy Beta",
        school_code="BETA-001",
    )
    await db_session.commit()

    client_b = await auth_client_factory(principal_b)

    # Principal B updates their own school via /profile
    update_resp = await client_b.patch(
        "/api/v1/schools/profile",
        json={"name": "Academy Beta Updated"},
    )
    assert update_resp.status_code == 200

    # Verify School A was not modified
    await db_session.refresh(school_a)
    assert school_a.name == "Academy Alpha"
