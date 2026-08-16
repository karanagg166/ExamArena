import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

import app.exams.crud as exam_crud
import app.sections.crud as crud
from app.api.deps import get_current_user
from app.core.models import Role
from app.exams.permissions import can_manage_exam
from app.sections.schemas import (
    SectionCreateRequest,
    SectionResponse,
    SectionUpdateRequest,
)
from app.teachers.crud import get_teacher_by_user_id
from app.users.schemas import UserResponse

router = APIRouter(prefix="/api/v1/sections", tags=["sections"])
logger = logging.getLogger(__name__)


async def _require_teacher(current_user: UserResponse):
    """Ensure the current user is a teacher and return their profile."""
    if current_user.role == Role.ADMIN:
        return None
    if current_user.role not in (Role.TEACHER, Role.PRINCIPAL):
        raise HTTPException(status_code=403, detail="Only teachers can manage sections")
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


@router.post("", response_model=SectionResponse, status_code=status.HTTP_201_CREATED)
async def create_new_section(
    section_data: SectionCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Create a section for an exam. Teachers only."""
    if not section_data.examId:
        raise HTTPException(
            status_code=400, detail="examId is required to create a section"
        )
    await _require_exam_manager(current_user, section_data.examId)
    return await crud.create_section(section_data)


@router.get("/exam/{exam_id}", response_model=list[SectionResponse])
async def get_exam_sections(
    exam_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get all sections for an exam, ordered by sortOrder."""
    return await crud.get_sections_by_exam(exam_id)


@router.get("/{section_id}", response_model=SectionResponse)
async def get_section(
    section_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get a single section by ID."""
    section = await crud.get_section_by_id(section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    return section


@router.patch("/{section_id}", response_model=SectionResponse)
async def patch_section(
    section_id: str,
    update_data: SectionUpdateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Update a section. Teachers only."""
    section = await crud.get_section_by_id(section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    await _require_exam_manager(current_user, section.examId)
    return await crud.update_section(section_id, update_data)


@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_section(
    section_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Delete a section and all its questions. Teachers only."""
    section = await crud.get_section_by_id(section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    await _require_exam_manager(current_user, section.examId)
    await crud.delete_section(section_id)
    return None
