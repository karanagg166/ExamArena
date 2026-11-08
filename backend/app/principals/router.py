from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

import app.core.database as db
from app.api.deps import get_current_user
from app.core.models import Role, School
from app.principals.crud import (
    create_principal,
    get_principal_by_teacher_id,
    update_principal,
)
from app.principals.schemas import (
    PrincipalCreateRequest,
    PrincipalProfileUpdate,
    PrincipalResponse,
)
from app.teachers.crud import get_teacher_by_user_id
from app.users.schemas import UserResponse

router = APIRouter(prefix="/api/v1/principals", tags=["principals"])


async def require_school_owner(user: UserResponse, school_id: str) -> None:
    async with db.get_session() as session:
        owner = await session.scalar(
            select(School.createdBy).where(School.id == school_id)
        )
    if user.role not in (Role.PRINCIPAL, Role.ADMIN) or owner != user.id:
        raise HTTPException(
            403, "Only the school's owner can initialize its principal profile."
        )


async def get_current_teacher_profile(current_user: UserResponse):
    teacher = await get_teacher_by_user_id(current_user.id)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found",
        )

    return teacher


@router.post("", response_model=PrincipalResponse, status_code=status.HTTP_201_CREATED)
async def create_my_principal_profile(
    data: PrincipalCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Create a principal profile for the current user."""
    teacher = await get_current_teacher_profile(current_user)

    existing = await get_principal_by_teacher_id(teacher.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Principal profile already exists",
        )
    await require_school_owner(current_user, data.schoolId)
    from app.teachers.crud import join_school

    await join_school(current_user.id, data.schoolId)
    return await create_principal(
        teacher_id=teacher.id,
        experience=data.experience,
        school_id=data.schoolId,
    )


@router.get("/me", response_model=PrincipalResponse)
async def get_my_principal_data(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get the current user's principal profile."""
    teacher = await get_current_teacher_profile(current_user)
    principal = await get_principal_by_teacher_id(teacher.id)
    if not principal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Principal profile not found. Please complete your profile setup.",
        )

    return principal


@router.put("/me", response_model=PrincipalResponse)
async def update_my_principal_data(
    principal_data: PrincipalProfileUpdate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Update the current user's principal profile."""
    teacher = await get_current_teacher_profile(current_user)

    existing = await get_principal_by_teacher_id(teacher.id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Principal profile not found",
        )

    return await update_principal(teacher.id, principal_data)
