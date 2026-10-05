"""Authorization helpers for question imports."""

from typing import Any

from fastapi import HTTPException, status

import app.exams.crud as exam_crud
from app.api.deps import enforce_rbac_permission
from app.core.models import Role
from app.exams.permissions import can_manage_exam
from app.exams.schemas import ExamResponse
from app.teachers.crud import get_teacher_by_user_id
from app.users.schemas import UserResponse


async def require_import_teacher(current_user: UserResponse) -> Any | None:
    """Enforces Casbin RBAC for question imports and returns the teacher entity if applicable."""
    enforce_rbac_permission(
        current_user.role,
        "question_imports",
        "create",
        "Only teachers and authorized managers can import question papers",
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


async def require_exam_import_access(
    current_user: UserResponse, exam_id: str
) -> tuple[Any | None, ExamResponse]:
    """Ensures the current user is authorized to manage the specified exam."""
    teacher = await require_import_teacher(current_user)
    exam = await exam_crud.get_exam_by_id(exam_id)
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )
    if not can_manage_exam(current_user, teacher, exam):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage this exam",
        )
    return teacher, exam
