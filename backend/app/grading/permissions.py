"""Teacher authorization helpers for student answer grading."""

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import enforce_rbac_permission
from app.core.models import Exam, Question, Role, StudentExam, StudentExamAnswer, Teacher
from app.exams.permissions import can_manage_exam
from app.teachers.crud import get_teacher_by_user_id
from app.users.schemas import UserResponse


async def require_grading_manager(current_user: UserResponse) -> Teacher | None:
    """Enforces Casbin RBAC for grading operations and returns the Teacher record."""
    enforce_rbac_permission(
        current_user.role,
        "grading",
        "grade",
        "Only authorized teachers, principals, or administrators can grade submissions",
    )
    if current_user.role == Role.ADMIN:
        return None

    teacher = await get_teacher_by_user_id(current_user.id)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher profile not found for current user",
        )
    return teacher


async def require_answer_grading_access(
    current_user: UserResponse,
    answer_id: str,
    session: AsyncSession,
) -> tuple[StudentExamAnswer, Teacher | None]:
    """Loads a student answer and verifies the user is authorized to grade the exam it belongs to."""
    teacher = await require_grading_manager(current_user)

    stmt = (
        select(StudentExamAnswer)
        .where(StudentExamAnswer.id == answer_id)
        .options(
            selectinload(StudentExamAnswer.question),
            selectinload(StudentExamAnswer.studentExam)
            .selectinload(StudentExam.exam)
            .selectinload(Exam.teacher),
        )
    )
    answer = (await session.execute(stmt)).scalar_one_or_none()

    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student answer not found",
        )

    student_exam = answer.studentExam
    if not student_exam or not student_exam.exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated exam not found for this answer",
        )

    exam = student_exam.exam
    if not can_manage_exam(current_user, teacher, exam):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to grade answers for this exam",
        )

    return answer, teacher
