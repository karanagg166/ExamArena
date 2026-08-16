from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

import app.attempts.crud as crud
from app.api.deps import get_current_user
from app.attempts.schemas import (
    StudentExamCreate,
    StudentExamResponse,
    StudentExamSubmit,
)
from app.core.models import Role
from app.students.crud import get_student_by_user_id
from app.users.schemas import UserResponse

router = APIRouter(prefix="/api/v1/attempts", tags=["attempts"])


@router.post(
    "/start", response_model=StudentExamResponse, status_code=status.HTTP_201_CREATED
)
async def start_exam(
    attempt_data: StudentExamCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    if current_user.role != Role.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can start exams")
    try:
        return await crud.start_exam_attempt(attempt_data, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{attempt_id}", response_model=StudentExamResponse)
async def get_attempt(
    attempt_id: str, current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    if current_user.role != Role.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can view attempts")
    attempt = await crud.get_attempt_by_id(attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    student = await get_student_by_user_id(current_user.id)
    if not student or attempt.studentId != student.id:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return attempt


@router.post("/submit", response_model=StudentExamResponse)
async def submit_exam(
    submit_data: StudentExamSubmit,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    if current_user.role != Role.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can submit exams")
    try:
        return await crud.submit_exam_attempt(submit_data, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
