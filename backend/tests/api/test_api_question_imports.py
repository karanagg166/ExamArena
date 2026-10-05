"""API-level tests for /api/v1/exams/{exam_id}/question-imports and /api/v1/question-imports/*."""

import io
import pytest

from app.core.models import Role
from tests.factories.exam_factory import create_exam_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_unauthenticated_cannot_import(client):
    res = await client.post(
        "/api/v1/exams/non-existent-exam/question-imports",
        files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4\n%%EOF"), "application/pdf")},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_import_missing_file_422(auth_client_factory, db_session):
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_api1@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-API-1")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_api1@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    res = await client.post(f"/api/v1/exams/{exam.id}/question-imports")
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_import_fake_pdf_signature_rejected(auth_client_factory, db_session):
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_api2@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-API-2")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_api2@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    fake_content = b"NOT A PDF HEADER"
    res = await client.post(
        f"/api/v1/exams/{exam.id}/question-imports",
        files={"file": ("fake.pdf", io.BytesIO(fake_content), "application/pdf")},
    )
    assert res.status_code == 415
    assert "signature" in res.json()["detail"].lower()



@pytest.mark.asyncio
async def test_get_nonexistent_import_404(auth_client_factory, db_session):
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_api3@dev.local")
    client = await auth_client_factory(teacher_user)
    res = await client.get("/api/v1/question-imports/non-existent-id")
    assert res.status_code == 404
