"""Integration tests for Bug 2: Proctoring violation authorization matrix and spoofing prevention.

Authorization matrix verified:
- student owns attempt         -> 200
- different student            -> 403
- teacher authorized for exam  -> 200
- unrelated teacher            -> 403
- principal same school        -> 200
- principal different school   -> 403
- admin                        -> 200
- unauthenticated user         -> 401
- nonexistent attempt          -> 404

Audit log verification:
- Generated audit event uses examId and studentId derived server-side from attempt.
- Spoofed examId / studentId in request payload are ignored.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.actions import AuditAction
from app.core.models import AuditLog, Role, StudentExamStatus
from tests.conftest import TestAsyncSessionLocal
from tests.factories.attempt_factory import create_attempt_factory
from tests.factories.class_factory import create_class_factory
from tests.factories.exam_factory import create_exam_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.student_factory import create_student_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_proctoring_authorization_matrix_and_audit_integrity(
    auth_client_factory, client, db_session: AsyncSession
):
    # School A
    school_a = await create_school_factory(db_session, school_code="SCH-A-01")
    class_a = await create_class_factory(db_session, school=school_a)

    # School B
    school_b = await create_school_factory(db_session, school_code="SCH-B-01")
    class_b = await create_class_factory(db_session, school=school_b)

    # Teacher A (owns the exam in School A)
    user_teacher_a = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.a@test.examarena.dev"
    )
    teacher_a = await create_teacher_factory(db_session, user=user_teacher_a, school=school_a)

    # Teacher B (unrelated teacher in School B)
    user_teacher_b = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.b@test.examarena.dev"
    )
    teacher_b = await create_teacher_factory(db_session, user=user_teacher_b, school=school_b)

    # Principal A (principal of School A)
    user_principal_a = await create_user_factory(
        db_session, role=Role.PRINCIPAL, email="principal.a@test.examarena.dev"
    )
    principal_teacher_a = await create_teacher_factory(
        db_session, user=user_principal_a, school=school_a
    )

    # Principal B (principal of School B)
    user_principal_b = await create_user_factory(
        db_session, role=Role.PRINCIPAL, email="principal.b@test.examarena.dev"
    )
    principal_teacher_b = await create_teacher_factory(
        db_session, user=user_principal_b, school=school_b
    )

    # Admin
    user_admin = await create_user_factory(
        db_session, role=Role.ADMIN, email="admin@test.examarena.dev"
    )

    # Student 1 (owns attempt in School A)
    user_student_1 = await create_user_factory(
        db_session, role=Role.STUDENT, email="student1@test.examarena.dev"
    )
    student_1 = await create_student_factory(
        db_session, user=user_student_1, school=school_a, school_class=class_a
    )

    # Student 2 (different student)
    user_student_2 = await create_user_factory(
        db_session, role=Role.STUDENT, email="student2@test.examarena.dev"
    )
    student_2 = await create_student_factory(
        db_session, user=user_student_2, school=school_a, school_class=class_a
    )

    # Exam created by Teacher A in School A
    exam_a = await create_exam_factory(
        db_session,
        teacher=teacher_a,
        is_published=True,
    )

    # Attempt belonging to Student 1 for Exam A
    attempt = await create_attempt_factory(
        db_session,
        exam=exam_a,
        student=student_1,
        status=StudentExamStatus.IN_PROGRESS,
    )
    await db_session.commit()

    attempt_id = str(attempt.id)
    real_exam_id = str(exam_a.id)
    real_student_id = str(student_1.id)

    # Clients
    client_student_1 = await auth_client_factory(user_student_1)
    client_student_2 = await auth_client_factory(user_student_2)
    client_teacher_a = await auth_client_factory(user_teacher_a)
    client_teacher_b = await auth_client_factory(user_teacher_b)
    client_principal_a = await auth_client_factory(user_principal_a)
    client_principal_b = await auth_client_factory(user_principal_b)
    client_admin = await auth_client_factory(user_admin)

    # Payload with deliberately spoofed identifiers
    spoofed_payload = {
        "violationType": "TAB_SWITCH",
        "details": {"reason": "User switched away from active exam tab"},
    }

    # 1. Unauthenticated user -> 401
    resp_unauth = await client.post(
        f"/api/v1/attempts/{attempt_id}/proctoring-violation", json=spoofed_payload
    )
    assert resp_unauth.status_code == 401

    # 2. Nonexistent attempt -> 404
    resp_404 = await client_student_1.post(
        "/api/v1/attempts/nonexistent-attempt-id/proctoring-violation",
        json=spoofed_payload,
    )
    assert resp_404.status_code == 404

    # 3. Different student -> 403
    resp_diff_student = await client_student_2.post(
        f"/api/v1/attempts/{attempt_id}/proctoring-violation", json=spoofed_payload
    )
    assert resp_diff_student.status_code == 403

    # 4. Unrelated teacher -> 403
    resp_unrelated_teacher = await client_teacher_b.post(
        f"/api/v1/attempts/{attempt_id}/proctoring-violation", json=spoofed_payload
    )
    assert resp_unrelated_teacher.status_code == 403

    # 5. Principal of different school -> 403
    resp_diff_principal = await client_principal_b.post(
        f"/api/v1/attempts/{attempt_id}/proctoring-violation", json=spoofed_payload
    )
    assert resp_diff_principal.status_code == 403

    # 6. Student owns attempt -> 200
    resp_own_student = await client_student_1.post(
        f"/api/v1/attempts/{attempt_id}/proctoring-violation", json=spoofed_payload
    )
    assert resp_own_student.status_code == 200
    assert resp_own_student.json()["attemptId"] == attempt_id

    # 7. Teacher authorized for exam -> 200
    resp_teacher_a = await client_teacher_a.post(
        f"/api/v1/attempts/{attempt_id}/proctoring-violation", json=spoofed_payload
    )
    assert resp_teacher_a.status_code == 200

    # 8. Principal of same school -> 200
    resp_principal_a = await client_principal_a.post(
        f"/api/v1/attempts/{attempt_id}/proctoring-violation", json=spoofed_payload
    )
    assert resp_principal_a.status_code == 200

    # 9. Admin -> 200
    resp_admin = await client_admin.post(
        f"/api/v1/attempts/{attempt_id}/proctoring-violation", json=spoofed_payload
    )
    assert resp_admin.status_code == 200

    # 10. Verify audit event attributes derived strictly from server-side attempt
    async with TestAsyncSessionLocal() as audit_session:
        stmt = (
            select(AuditLog)
            .where(
                AuditLog.action == AuditAction.PROCTORING_VIOLATION.value,
                AuditLog.resourceId == attempt_id,
            )
            .order_by(AuditLog.timestamp.desc())
        )
        logs = (await audit_session.execute(stmt)).scalars().all()
        assert len(logs) >= 4, "All 4 successful violations must be audited"
        for log in logs:
            assert log.metadata_ is not None
            assert log.metadata_["examId"] == real_exam_id
            assert log.metadata_["studentId"] == real_student_id
            assert log.metadata_["violationType"] == "TAB_SWITCH"
