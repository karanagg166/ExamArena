"""Integration tests for School Classes, unique join codes, and roll numbers."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Role
from tests.factories.class_factory import create_class_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_class_creation_and_auto_joincode(
    auth_client_factory, db_session: AsyncSession
):
    """Verify creating a class generates a unique 8-character uppercase join code and sets initial nextRollNo to 1."""
    principal = await create_user_factory(
        db_session,
        role=Role.PRINCIPAL,
        email="principal.school@test.examarena.dev",
    )
    school = await create_school_factory(
        db_session, creator_user=principal, school_code="CLS-999"
    )
    await db_session.commit()

    client = await auth_client_factory(principal)

    class_payload = {
        "name": "Grade 10 Mathematics",
        "year": "2026",
        "section": "A",
        "schoolId": school.id,
    }
    resp = await client.post("/api/v1/classes", json=class_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Grade 10 Mathematics"
    assert data["year"] == "2026"
    assert data["section"] == "A"
    assert data["schoolId"] == school.id
    assert len(data["joinCode"]) == 8
    assert data["joinCode"].isupper()
    assert data["nextRollNo"] == 1


@pytest.mark.asyncio
async def test_duplicate_class_section_in_same_year_rejected(
    auth_client_factory, db_session: AsyncSession
):
    """Verify duplicate [schoolId, year, section] returns 400 Bad Request."""
    principal = await create_user_factory(
        db_session,
        role=Role.PRINCIPAL,
        email="principal.dup@test.examarena.dev",
    )
    school = await create_school_factory(
        db_session, creator_user=principal, school_code="DUP-001"
    )
    await create_class_factory(
        db_session,
        school=school,
        name="Grade 9",
        year="2026",
        section="B",
    )
    await db_session.commit()

    client = await auth_client_factory(principal)

    duplicate_payload = {
        "name": "Another Grade 9",
        "year": "2026",
        "section": "B",
        "schoolId": school.id,
    }
    resp = await client.post("/api/v1/classes", json=duplicate_payload)
    assert resp.status_code in (400, 409)
    assert "already exists" in resp.json()["detail"].lower()
