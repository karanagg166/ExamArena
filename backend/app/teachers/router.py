from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.teachers.crud import (
    create_teacher,
    get_all_qualifications,
    get_all_subjects,
    get_teacher_by_user_id,
    get_teachers,
    join_school,
    update_teacher,
)
from app.teachers.crud import get_teacher_by_id as crud_get_teacher_by_id
from app.teachers.schemas import (
    TeacherCreate,
    TeacherCreateRequest,
    TeacherFilterParams,
    TeacherJoinSchoolRequest,
    TeacherListItemResponse,
    TeacherResponse,
    TeacherUpdate,
)
from app.users.schemas import UserResponse

router = APIRouter(prefix="/api/v1/teachers", tags=["teachers"])


@router.get("/", response_model=list[TeacherListItemResponse])
async def fetch_teachers(
    filters: Annotated[TeacherFilterParams, Depends()],
    _current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    return await get_teachers(filters)


@router.post("/", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_my_teacher_profile(
    teacher_data: TeacherCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Create teacher profile for the currently logged-in user"""
    existing = await get_teacher_by_user_id(current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Teacher profile already exists",
        )
    create_payload = TeacherCreate(**teacher_data.model_dump(), userId=current_user.id)
    return await create_teacher(create_payload)


@router.get("/me", response_model=TeacherResponse)
async def get_my_teacher_data(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get current user's teacher data"""
    teacher = await get_teacher_by_user_id(current_user.id)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found. Please complete your profile setup.",
        )
    return teacher


@router.post("/me/join-school", response_model=TeacherResponse)
async def join_my_school(
    payload: TeacherJoinSchoolRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Assign current teacher profile to the selected school."""
    updated_teacher = await join_school(current_user.id, payload.school_id)
    if updated_teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found. Please complete your profile setup.",
        )
    if updated_teacher is False:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        )
    return updated_teacher


@router.put("/me", response_model=TeacherResponse)
async def update_my_teacher_data(
    teacher_data: TeacherUpdate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Update current user's teacher data"""
    existing = await get_teacher_by_user_id(current_user.id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher profile not found"
        )
    return await update_teacher(current_user.id, teacher_data)


@router.get("/qualifications", response_model=list[str])
async def get_teacher_qualifications():
    """Get all possible qualifications for teachers"""
    return await get_all_qualifications()


@router.get("/subjects", response_model=list[str])
async def get_teacher_subjects():
    """Get all possible subjects for teachers"""
    return await get_all_subjects()


@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher_by_id(
    teacher_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get teacher data by primary ID"""
    del current_user
    teacher = await crud_get_teacher_by_id(teacher_id)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found"
        )
    return teacher
