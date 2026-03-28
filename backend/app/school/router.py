from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

import app.core.database as db
from app.api.deps import get_current_user
from app.principals.crud import create_principal, get_principal_by_teacher_id
from app.school import crud
from app.school.schemas import SchoolCreateRequest, SchoolResponse, SchoolUpdateRequest
from app.teachers.crud import get_teacher_by_user_id
from app.users.schemas import UserResponse

router = APIRouter(prefix="/api/v1/schools", tags=["Schools"])

# ==========================================
# 1. SELF-SERVICE ROUTES (Using JWT Token)
# ==========================================

@router.post("/", response_model=SchoolResponse, status_code=status.HTTP_201_CREATED)
async def create_school(
    school_data: SchoolCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """Create a new school. (Fails if the user already manages one)."""
    teacher = await get_teacher_by_user_id(current_user.id)
    if teacher:
        principal = await get_principal_by_teacher_id(teacher.id)
        if not principal:
            await create_principal(teacher.id, 0)

    existing_school = await crud.get_school_by_user_id(current_user.id)
    if existing_school:
        raise HTTPException(status_code=400, detail="User already manages a school.")

    return await crud.create_school(school_data, current_user.id)


@router.get("/profile", response_model=SchoolResponse)
async def get_my_school_profile(
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """Get the school profile managed by the currently logged-in user."""
    school = await crud.get_school_by_user_id(current_user.id)
    if not school:
        raise HTTPException(status_code=404, detail="School profile not found.")

    return school


@router.patch("/profile", response_model=SchoolResponse)
async def update_my_school_profile(
    school_data: SchoolUpdateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """Update the school profile for the currently logged-in user."""
    school = await crud.get_school_by_user_id(current_user.id)
    if not school:
        raise HTTPException(status_code=404, detail="School profile not found.")

    updated_school = await crud.update_school(school.id, school_data)
    if not updated_school:
        raise HTTPException(status_code=500, detail="Failed to update school.")

    return updated_school


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_school_profile(
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """Delete the school managed by the currently logged-in user."""
    school = await crud.get_school_by_user_id(current_user.id)
    if not school:
        raise HTTPException(status_code=404, detail="School profile not found.")

    await crud.delete_school(school.id)
    return None


# ==========================================
# 2. LOOKUP ROUTES (For searching & joining)
# ==========================================

@router.get("/", response_model=list[SchoolResponse])
async def get_all_schools(
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """Get a list of every school in the system. (Admin/System use)."""
    return await crud.get_all_schools()


@router.get("/search", response_model=SchoolResponse)
async def search_school_by_name(
    name: str, # Passed as a query parameter: /api/v1/schools/search?name=Springfield High
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """Find a school by its exact name."""
    school = await crud.get_school_by_name(name)
    if not school:
        raise HTTPException(status_code=404, detail="School not found with that name.")
    return school


@router.get("/code/{code}", response_model=SchoolResponse)
async def get_school_by_join_code(
    code: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """Look up a school by its unique join code (Crucial for Student Onboarding)."""
    school = await crud.get_school_by_code(code)
    if not school:
        raise HTTPException(status_code=404, detail="Invalid School Code.")
    return school


# 🚨 DYNAMIC ROUTE MUST GO LAST 🚨
@router.get("/{school_id}", response_model=SchoolResponse)
async def get_school_by_id(
    school_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """Get a specific school by its database ID."""
    school = await crud.get_school_by_id(school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found.")
    return school


# ==========================================
# 3. CLASS LOOKUP (For student onboarding)
# ==========================================

class SchoolClassResponse(BaseModel):
    id: str
    name: str
    schoolId: str

    class Config:
        from_attributes = True


@router.get("/{school_id}/classes", response_model=list[SchoolClassResponse])
async def get_classes_for_school(
    school_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """Get all classes for a school. Used by students during onboarding."""
    school = await crud.get_school_by_id(school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found.")

    classes = await db.prisma.schoolclass.find_many(
        where={"schoolId": school_id}
    )
    return classes
