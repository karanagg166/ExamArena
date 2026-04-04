from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from app.api.deps import get_current_user
from app.users.schemas import UserResponse
import app.questions.crud as crud
from app.questions.schemas import QuestionCreateRequest, QuestionResponse, QuestionUpdateRequest

router = APIRouter(prefix="/api/v1/questions", tags=["questions"])

@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def add_new_question(
    question_data: QuestionCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    if not question_data.examId:
        raise HTTPException(status_code=400, detail="examId is required to create a question")
    return await crud.create_question(question_data)


@router.patch("/{question_id}", response_model=QuestionResponse)
async def patch_question(
    question_id: str,
    update_data: QuestionUpdateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    question = await crud.get_question_by_id(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return await crud.update_question(question_id, update_data)

@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_question(
    question_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    question = await crud.get_question_by_id(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    await crud.delete_question(question_id)
    return None
