from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status  # type: ignore

import app.exams.crud as crud
from app.api.deps import get_current_user
from app.exams.schemas import ExamCreateRequest, ExamResponse, ExamUpdateRequest
from app.teachers.crud import get_teacher_by_user_id
from app.users.schemas import UserResponse

router = APIRouter(prefix="/api/v1/exams", tags=["exams"])

async def get_teacher_from_user(user: UserResponse):
    teacher = await get_teacher_by_user_id(user.id)
    if not teacher:
        raise HTTPException(status_code=403, detail="Only teachers can manage exams")
    return teacher

@router.post("/", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_new_exam(
    exam_data: ExamCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    teacher = await get_teacher_from_user(current_user)
    return await crud.create_exam(exam_data, teacher.id)

@router.get("/", response_model=list[ExamResponse])
async def list_my_exams_teacher(
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    teacher = await get_teacher_from_user(current_user)
    return await crud.get_exams_by_teacher(teacher.id)

@router.get("/public/", response_model=list[ExamResponse])
async def list_published_exams(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    name: str | None = None,
    type: str | None = None,
    teacher_name: str | None = None,
    school_name: str | None = None,
    subject: str | None = None
):
    return await crud.get_published_exams(
        name=name,
        exam_type=type, # type: ignore
        teacher_name=teacher_name,
        school_name=school_name,
        subject=subject # type: ignore
    )

@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):  
    exam = await crud.get_exam_by_id(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam

@router.patch("/{exam_id}", response_model=ExamResponse)
async def patch_exam(
    exam_id: str,
    update_data: ExamUpdateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    teacher = await get_teacher_from_user(current_user)
    exam = await crud.get_exam_by_id(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    if exam.teacherId != teacher.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this exam")
    return await crud.update_exam(exam_id, update_data)
