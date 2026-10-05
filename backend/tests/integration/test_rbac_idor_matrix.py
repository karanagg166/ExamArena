"""Integration tests for RBAC, IDOR prevention, and cross-role authorization matrix."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Role
from tests.factories.attempt_factory import create_attempt_factory
from tests.factories.exam_factory import create_exam_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.student_factory import create_student_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_student_cannot_create_exam_returns_403(
    auth_client_factory, db_session: AsyncSession
):
    """Verify Student role receives 403 Forbidden when attempting to create an exam."""
    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="student.rbac@test.examarena.dev"
    )
    await db_session.commit()

    client = await auth_client_factory(student_user)

    exam_payload = {
        "name": "Unauthorized Exam",
        "description": "Student trying to create exam",
        "scheduledAt": "2026-10-01T10:00:00Z",
        "duration": 60,
        "maxMarks": 100,
        "subject": "MATHS",
        "type": "MIDTERM",
    }
    resp = await client.post("/api/v1/exams", json=exam_payload)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_student_cannot_create_question_returns_403(
    auth_client_factory, db_session: AsyncSession
):
    """Verify Student role receives 403 Forbidden when attempting to add questions."""
    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="stud.q@test.examarena.dev"
    )
    exam = await create_exam_factory(db_session)
    await db_session.commit()

    client = await auth_client_factory(student_user)

    question_payload = {
        "examId": exam.id,
        "questionNumber": 1,
        "text": "Unauthorized Question?",
        "marks": 5,
        "questionType": "MULTIPLE_CHOICE",
        "options": [
            {"text": "Option 1", "optionNumber": 1, "isCorrect": True},
            {"text": "Option 2", "optionNumber": 2, "isCorrect": False},
        ],
    }
    resp = await client.post("/api/v1/questions", json=question_payload)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_teacher_idor_cannot_edit_other_teacher_exam(
    auth_client_factory, db_session: AsyncSession
):
    """Verify Teacher B cannot modify an exam created by Teacher A in a different school."""
    teacher_a = await create_teacher_factory(db_session)
    teacher_b_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.b@test.examarena.dev"
    )
    teacher_b = await create_teacher_factory(db_session, user=teacher_b_user)

    exam_a = await create_exam_factory(
        db_session, teacher=teacher_a, name="Teacher A Exam"
    )
    await db_session.commit()

    client_b = await auth_client_factory(teacher_b_user)

    resp = await client_b.patch(
        f"/api/v1/exams/{exam_a.id}",
        json={"name": "Hacked Exam Name"},
    )
    assert resp.status_code == 403

    # Verify Exam A name remains unchanged
    await db_session.refresh(exam_a)
    assert exam_a.name == "Teacher A Exam"


@pytest.mark.asyncio
async def test_get_attempt_staff_and_student_authorization_matrix(
    auth_client_factory, db_session: AsyncSession
):
    """Verify authorization matrix for viewing exam attempts:
    - Student A (attempt owner) -> 200 with redaction
    - Student B (different student) -> 404 (IDOR protection)
    - Teacher A (exam creator) -> 200 with full attempt
    - Teacher B (unrelated teacher) -> 403 Forbidden
    - Principal A (same school as Teacher A) -> 200 with full attempt
    - Principal B (different school) -> 403 Forbidden
    - Admin -> 200 with full attempt
    """
    # School A and Principal A
    principal_a_user = await create_user_factory(
        db_session, role=Role.PRINCIPAL, email="principal.a@test.examarena.dev"
    )
    school_a = await create_school_factory(
        db_session, creator_user=principal_a_user, name="School Alpha"
    )

    # Teacher A in School A
    teacher_a_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.a@test.examarena.dev"
    )
    teacher_a = await create_teacher_factory(
        db_session, user=teacher_a_user, school=school_a
    )

    # Exam created by Teacher A
    exam = await create_exam_factory(db_session, teacher=teacher_a, is_public=True)

    # Student A in School A
    student_a_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="student.a@test.examarena.dev"
    )
    student_a = await create_student_factory(
        db_session, user=student_a_user, school=school_a
    )

    # Attempt by Student A (results not released)
    attempt = await create_attempt_factory(
        db_session, exam=exam, student=student_a, marks_obtained=85.0
    )

    # Student B (different student)
    student_b_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="student.b@test.examarena.dev"
    )
    await create_student_factory(db_session, user=student_b_user)

    # Teacher B (different school/unrelated)
    teacher_b_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.b.unrelated@test.examarena.dev"
    )
    await create_teacher_factory(db_session, user=teacher_b_user)

    # School B and Principal B
    principal_b_user = await create_user_factory(
        db_session, role=Role.PRINCIPAL, email="principal.b@test.examarena.dev"
    )
    await create_school_factory(
        db_session, creator_user=principal_b_user, name="School Beta"
    )

    # Admin user
    admin_user = await create_user_factory(
        db_session, role=Role.ADMIN, email="admin.matrix@test.examarena.dev"
    )

    await db_session.commit()

    # 1. Student A (owner) -> 200 with redaction
    client_student_a = await auth_client_factory(student_a_user)
    resp_student_a = await client_student_a.get(f"/api/v1/attempts/{attempt.id}")
    assert resp_student_a.status_code == 200
    data_student_a = resp_student_a.json()
    assert data_student_a["id"] == attempt.id
    # Redaction before results released: marksObtained must be None
    assert data_student_a["marksObtained"] is None

    # 2. Student B (different student) -> 404
    client_student_b = await auth_client_factory(student_b_user)
    resp_student_b = await client_student_b.get(f"/api/v1/attempts/{attempt.id}")
    assert resp_student_b.status_code == 404

    # 3. Teacher A (exam creator) -> 200 with full details
    client_teacher_a = await auth_client_factory(teacher_a_user)
    resp_teacher_a = await client_teacher_a.get(f"/api/v1/attempts/{attempt.id}")
    assert resp_teacher_a.status_code == 200
    data_teacher_a = resp_teacher_a.json()
    assert data_teacher_a["id"] == attempt.id
    assert data_teacher_a["marksObtained"] == 85.0

    # 4. Teacher B (unrelated teacher) -> 403
    client_teacher_b = await auth_client_factory(teacher_b_user)
    resp_teacher_b = await client_teacher_b.get(f"/api/v1/attempts/{attempt.id}")
    assert resp_teacher_b.status_code == 403

    # 5. Principal A (same school as Teacher A) -> 200
    client_principal_a = await auth_client_factory(principal_a_user)
    resp_principal_a = await client_principal_a.get(f"/api/v1/attempts/{attempt.id}")
    assert resp_principal_a.status_code == 200
    data_principal_a = resp_principal_a.json()
    assert data_principal_a["id"] == attempt.id
    assert data_principal_a["marksObtained"] == 85.0

    # 6. Principal B (different school) -> 403
    client_principal_b = await auth_client_factory(principal_b_user)
    resp_principal_b = await client_principal_b.get(f"/api/v1/attempts/{attempt.id}")
    assert resp_principal_b.status_code == 403

    # 7. Admin -> 200
    client_admin = await auth_client_factory(admin_user)
    resp_admin = await client_admin.get(f"/api/v1/attempts/{attempt.id}")
    assert resp_admin.status_code == 200
    data_admin = resp_admin.json()
    assert data_admin["id"] == attempt.id
    assert data_admin["marksObtained"] == 85.0

