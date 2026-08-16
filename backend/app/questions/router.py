import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

import app.exams.crud as exam_crud
import app.questions.crud as crud
from app.api.deps import get_current_user
from app.core.models import Role
from app.exams.permissions import can_manage_exam
from app.questions.schemas import (
    QuestionCreateRequest,
    QuestionResponse,
    QuestionUpdateRequest,
)
from app.teachers.crud import get_teacher_by_user_id
from app.users.schemas import UserResponse

router = APIRouter(prefix="/api/v1/questions", tags=["questions"])
logger = logging.getLogger(__name__)


async def _require_teacher(current_user: UserResponse):
    """Ensure the current user is a teacher and return their profile."""
    if current_user.role == Role.ADMIN:
        return None
    if current_user.role not in (Role.TEACHER, Role.PRINCIPAL):
        raise HTTPException(
            status_code=403, detail="Only teachers can manage questions"
        )
    teacher = await get_teacher_by_user_id(current_user.id)
    if not teacher:
        raise HTTPException(status_code=403, detail="Teacher profile not found")
    return teacher


async def _require_exam_manager(current_user: UserResponse, exam_id: str) -> None:
    teacher = await _require_teacher(current_user)
    exam = await exam_crud.get_exam_by_id(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    if not can_manage_exam(current_user, teacher, exam):
        raise HTTPException(
            status_code=403, detail="Not authorized to manage this exam"
        )


@router.post("", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def add_new_question(
    question_data: QuestionCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Add a question to an exam. Teachers only."""
    if not question_data.examId:
        raise HTTPException(
            status_code=400, detail="examId is required to create a question"
        )
    await _require_exam_manager(current_user, question_data.examId)
    return await crud.create_question(question_data)


@router.patch("/{question_id}", response_model=QuestionResponse)
async def patch_question(
    question_id: str,
    update_data: QuestionUpdateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Update a question. Teachers only."""
    question = await crud.get_question_by_id(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if not question.examId:
        raise HTTPException(status_code=409, detail="Question is not linked to an exam")
    await _require_exam_manager(current_user, question.examId)
    return await crud.update_question(question_id, update_data)


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_question(
    question_id: str, current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """Delete a question. Teachers only."""
    question = await crud.get_question_by_id(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if not question.examId:
        raise HTTPException(status_code=409, detail="Question is not linked to an exam")
    await _require_exam_manager(current_user, question.examId)
    await crud.delete_question(question_id)
    return None
