"""Integration tests for Bug 3: Exam access password hashing, security, and lifecycle.

Invariants verified:
1. Private exam creation stores hash, not plaintext in DB.
2. Returned ExamResponse never contains stored hash or plaintext password.
3. Student starts private exam with correct password -> succeeds (201).
4. Incorrect password rejected (400).
5. Empty password rejected (400).
6. Password comparison is case-sensitive (e.g. SecretPass vs secretpass).
7. Public exam does not require password to start.
8. Editing an unrelated field on private exam preserves existing password hash.
9. Setting a new password replaces old hash.
10. Old password stops working after replacement, new password works.
11. Public and student exam endpoints never expose accessPassword or its hash.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Exam, Role
from app.core.security import verify_password
from tests.conftest import TestAsyncSessionLocal
from tests.factories.class_factory import create_class_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.student_factory import create_student_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_exam_access_password_security_lifecycle(
    auth_client_factory, client, db_session: AsyncSession
):
    school = await create_school_factory(db_session, school_code="SEC-PWD-01")
    school_class = await create_class_factory(db_session, school=school)

    # Teacher setup
    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.secpwd@test.examarena.dev"
    )
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)

    # Student setup
    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="student.secpwd@test.examarena.dev"
    )
    student = await create_student_factory(
        db_session, user=student_user, school=school, school_class=school_class
    )
    await db_session.commit()

    teacher_client = await auth_client_factory(teacher_user)
    student_client = await auth_client_factory(student_user)

    # ── 1. Create Private Exam with password ───────────────────────────────────
    raw_password = "SecretExamKey#2026"
    create_payload = {
        "name": "Classified Calculus Final",
        "description": "Comprehensive protected calculus exam",
        "scheduledAt": "2026-01-01T00:00:00Z",
        "duration": 60,
        "maxMarks": 100,
        "isPublished": True,
        "isPublic": False,
        "accessPassword": raw_password,
        "subject": "MATHS",
        "type": "FINAL",
        "questions": [],
    }

    create_resp = await teacher_client.post("/api/v1/exams", json=create_payload)
    assert create_resp.status_code == 201
    created_exam = create_resp.json()
    exam_id = created_exam["id"]

    # ── 2. Returned ExamResponse never contains raw password or hash ───────────
    assert created_exam["accessPassword"] is None, "accessPassword must be redacted in response"
    assert created_exam["hasAccessPassword"] is True

    # ── 3. Verify DB stores hash, not plaintext ────────────────────────────────
    async with TestAsyncSessionLocal() as verify_session:
        db_exam = (
            await verify_session.execute(select(Exam).where(Exam.id == exam_id))
        ).scalar_one()
        assert db_exam.accessPassword != raw_password, "Raw password must not be stored in plaintext"
        assert verify_password(raw_password, db_exam.accessPassword), "Database must store verifiable bcrypt hash"

    # ── 4. Public and Student endpoints never expose accessPassword ───────────
    # A) Student GET /api/v1/exams/{id}
    student_exam_resp = await student_client.get(f"/api/v1/exams/{exam_id}")
    assert student_exam_resp.status_code == 200
    st_exam_data = student_exam_resp.json()
    assert st_exam_data["accessPassword"] is None
    assert st_exam_data["hasAccessPassword"] is True

    # B) Student GET /api/v1/exams/public (published list)
    student_list_resp = await student_client.get("/api/v1/exams/public")
    assert student_list_resp.status_code == 200
    for e in student_list_resp.json():
        assert e["accessPassword"] is None

    # ── 5. Student start attempts ──────────────────────────────────────────────
    # A) Empty / missing password rejected
    resp_empty_pwd = await student_client.post(
        "/api/v1/attempts/start",
        json={"examId": exam_id, "accessPassword": ""},
    )
    assert resp_empty_pwd.status_code == 400
    assert "password" in resp_empty_pwd.json()["detail"].lower()

    # B) Incorrect password rejected
    resp_wrong_pwd = await student_client.post(
        "/api/v1/attempts/start",
        json={"examId": exam_id, "accessPassword": "WrongPassword123!"},
    )
    assert resp_wrong_pwd.status_code == 400
    assert "password" in resp_wrong_pwd.json()["detail"].lower()

    # C) Password comparison is case-sensitive
    resp_case_mismatch = await student_client.post(
        "/api/v1/attempts/start",
        json={"examId": exam_id, "accessPassword": raw_password.lower()},
    )
    assert resp_case_mismatch.status_code == 400

    # D) Correct password succeeds
    resp_correct_pwd = await student_client.post(
        "/api/v1/attempts/start",
        json={"examId": exam_id, "accessPassword": raw_password},
    )
    assert resp_correct_pwd.status_code == 201
    assert resp_correct_pwd.json()["examId"] == exam_id

    # ── 6. Editing unrelated field preserves existing password hash ────────────
    patch_resp = await teacher_client.patch(
        f"/api/v1/exams/{exam_id}",
        json={"description": "Updated exam description"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["hasAccessPassword"] is True
    assert patch_resp.json()["accessPassword"] is None

    async with TestAsyncSessionLocal() as verify_session:
        db_exam_after_edit = (
            await verify_session.execute(select(Exam).where(Exam.id == exam_id))
        ).scalar_one()
        assert verify_password(raw_password, db_exam_after_edit.accessPassword), (
            "Unrelated edit must preserve existing password hash"
        )

    # ── 7. Setting new password replaces old hash ──────────────────────────────
    new_password = "BrandNewSecretKey#999"
    patch_new_pwd_resp = await teacher_client.patch(
        f"/api/v1/exams/{exam_id}",
        json={"accessPassword": new_password},
    )
    assert patch_new_pwd_resp.status_code == 200
    assert patch_new_pwd_resp.json()["hasAccessPassword"] is True
    assert patch_new_pwd_resp.json()["accessPassword"] is None

    async with TestAsyncSessionLocal() as verify_session:
        db_exam_new_pwd = (
            await verify_session.execute(select(Exam).where(Exam.id == exam_id))
        ).scalar_one()
        assert not verify_password(raw_password, db_exam_new_pwd.accessPassword), (
            "Old password must no longer be verifiable"
        )
        assert verify_password(new_password, db_exam_new_pwd.accessPassword), (
            "New password must be verifiable"
        )

    # ── 8. Public exam does not require password ───────────────────────────────
    public_exam_payload = {
        "name": "Open Physics Quiz",
        "description": "Public quiz open to all students",
        "scheduledAt": "2026-01-01T00:00:00Z",
        "duration": 30,
        "maxMarks": 50,
        "isPublished": True,
        "isPublic": True,
        "subject": "SCIENCE",
        "type": "QUIZ",
        "questions": [],
    }
    public_exam_resp = await teacher_client.post("/api/v1/exams", json=public_exam_payload)
    assert public_exam_resp.status_code == 201
    public_exam = public_exam_resp.json()
    assert public_exam["hasAccessPassword"] is False

    # Second student starts public exam without password
    user_student_2 = await create_user_factory(
        db_session, role=Role.STUDENT, email="student2.secpwd@test.examarena.dev"
    )
    await create_student_factory(
        db_session, user=user_student_2, school=school, school_class=school_class
    )
    await db_session.commit()
    student_2_client = await auth_client_factory(user_student_2)

    resp_public_start = await student_2_client.post(
        "/api/v1/attempts/start",
        json={"examId": public_exam["id"]},
    )
    assert resp_public_start.status_code == 201
