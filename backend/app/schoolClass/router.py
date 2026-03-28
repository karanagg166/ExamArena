from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.schoolClass.crud import create_school_class, get_school_classes_by_school_id, get_school_class_by_id
from app.schoolClass.schemas import SchoolClassCreateRequest, SchoolClassResponse
from app.users.schemas import UserResponse


router = APIRouter(prefix="/api/v1/classes", tags=["classes"])


@router.post("/", response_model=SchoolClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    class_data: SchoolClassCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Create a new school class."""
    print("Received class creation request:", class_data, "from user:", current_user.id)
    created_class = await create_school_class(class_data, current_user.id)
    if not created_class:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create classes for your own school.",
        )

    return created_class


@router.get("/school/{school_id}", response_model=list[SchoolClassResponse])
async def get_classes_for_school(
    school_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get all classes for a specific school."""
    del current_user
    return await get_school_classes_by_school_id(school_id)


@router.get("/{class_id}", response_model=SchoolClassResponse)
async def get_class_by_id(
    class_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get a specific class by ID with RBAC stringency."""
    school_class = await get_school_class_by_id(class_id)
    if not school_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")



    return school_class
