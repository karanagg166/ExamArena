from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.principals.crud import (
    create_principal,
    get_principal_by_teacher_id,
    update_principal,
)
from app.principals.schemas import PrincipalUpdate
from app.school import crud
from app.school.schemas import (
    SchoolCreateRequest,
    SchoolFilterParams,
    SchoolResponse,
    SchoolType,
    SchoolUpdateRequest,
)
from app.schoolClass.crud import get_school_classes_by_school_id
from app.schoolClass.schemas import SchoolClassResponse
from app.teachers.crud import get_teacher_by_user_id
from app.users.schemas import UserResponse

router = APIRouter(prefix="/api/v1/schools", tags=["schools"])


@router.get("/me", response_model=SchoolResponse)
async def get_current_user_school(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> SchoolResponse:
    school = await crud.get_school_by_user_id(current_user.id)
    print("Current school:", school)
    if not school:
        raise HTTPException(status_code=404, detail="School profile not found.")

    return school


@router.post("/", response_model=SchoolResponse, status_code=status.HTTP_201_CREATED)
async def create_school(
    school_data: SchoolCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Create a school for the authenticated user."""
    existing_school = await crud.get_school_by_user_id(current_user.id)
    if existing_school:
        raise HTTPException(status_code=400, detail="User already manages a school.")

    school = await crud.create_school(school_data, current_user.id)

    teacher = await get_teacher_by_user_id(current_user.id)
    if teacher:
        principal = await get_principal_by_teacher_id(teacher.id)
        if not principal:
            await create_principal(teacher.id, experience=0, school_id=school.id)
        elif principal.schoolId != school.id:
            await update_principal(
                teacher.id,
                PrincipalUpdate(schoolId=school.id),
            )

    return school


@router.get("/profile", response_model=SchoolResponse)
async def get_my_school_profile(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get the current user's school."""
    return await get_current_user_school(current_user)


@router.patch("/me", response_model=SchoolResponse)
@router.patch("/profile", response_model=SchoolResponse)
async def update_my_school_profile(
    school_data: SchoolUpdateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Update the current user's school."""
    school = await get_current_user_school(current_user)
    updated_school = await crud.update_school(school.id, school_data)
    if not updated_school:
        raise HTTPException(status_code=500, detail="Failed to update school.")

    return updated_school


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_school_profile(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Delete the current user's school."""
    school = await get_current_user_school(current_user)
    await crud.delete_school(school.id)
    return None


@router.get("/", response_model=list[SchoolResponse])
async def fetch_schools(
    name: str | None = Query(None),
    city: str | None = Query(None),
    state: str | None = Query(None),
    country: str | None = Query(None),
    pincode: str | None = Query(None),
    school_code: str | None = Query(None, alias="schoolCode"),
    school_type: SchoolType | None = Query(None, alias="schoolType"),
    email: str | None = Query(None),
    website: str | None = Query(None),
    current_user=Depends(get_current_user),
):
    filters = SchoolFilterParams(
        name=name,
        city=city,
        state=state,
        country=country,
        pincode=pincode,
        school_code=school_code,
        school_type=school_type,
        email=email,
        website=website,
    )
    return await crud.get_schools(filters)


@router.get("/search", response_model=SchoolResponse)
async def search_school_by_name(
    name: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Find a school by exact name."""
    del current_user
    school = await crud.get_school_by_name(name)
    if not school:
        raise HTTPException(status_code=404, detail="School not found with that name.")

    return school


@router.get("/code/{code}", response_model=SchoolResponse)
async def get_school_by_join_code(
    code: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Look up a school by join code."""
    del current_user
    school = await crud.get_school_by_code(code)
    if not school:
        raise HTTPException(status_code=404, detail="Invalid school code.")

    return school


@router.get("/{school_id}", response_model=SchoolResponse)
async def get_school_by_id(
    school_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    print("Fetching school with ID:", school_id)  # Debug log
    """Get a school by database ID."""
    del current_user
    school = await crud.get_school_by_id(school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found.")

    return school


@router.get("/{school_id}/classes", response_model=list[SchoolClassResponse])
async def get_classes_for_school(
    school_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get all classes that belong to a school."""
    del current_user
    school = await crud.get_school_by_id(school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found.")

    return await get_school_classes_by_school_id(school_id)
