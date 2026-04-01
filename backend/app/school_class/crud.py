import app.core.database as db
from app.school.crud import get_school_by_user_id

from .schemas import (
    SchoolClassCreateRequest,
    SchoolClassResponse,
    SchoolClassUpdateRequest,
)


async def create_school_class(
    class_data: SchoolClassCreateRequest, user_id: str
) -> SchoolClassResponse | None:
    """Create a class for the authenticated user's school."""
    data_dict = class_data.model_dump()

    school = await get_school_by_user_id(user_id)
    if not school:
        return None
    data_dict["schoolId"] = school.id
    school_class = await db.prisma.schoolclass.create(data=data_dict)  # type: ignore
    return SchoolClassResponse.model_validate(school_class)


async def get_school_classes_by_school_id(school_id: str) -> list[SchoolClassResponse]:
    """Get all classes for a school."""
    classes = await db.prisma.schoolclass.find_many(where={"schoolId": school_id})
    return [
        SchoolClassResponse.model_validate(school_class) for school_class in classes
    ]


async def get_school_class_by_id(class_id: str) -> SchoolClassResponse | None:
    """Get a specific class by its ID."""
    school_class = await db.prisma.schoolclass.find_unique(where={"id": class_id})
    if not school_class:
        return None
    return SchoolClassResponse.model_validate(school_class)


async def update_school_class(
    class_id: str, class_data: SchoolClassUpdateRequest, user_id: str
) -> SchoolClassResponse | None:
    """Update a class that belongs to the authenticated user's school."""
    update_dict = class_data.model_dump(exclude_unset=True)
    if not update_dict:
        return None

    school = await get_school_by_user_id(user_id)
    if not school:
        return None

    school_class = await db.prisma.schoolclass.find_unique(where={"id": class_id})
    if not school_class or school_class.schoolId != school.id:
        return None

    updated_class = await db.prisma.schoolclass.update(
        where={"id": class_id}, data=update_dict  # type: ignore
    )
    return SchoolClassResponse.model_validate(updated_class)


async def delete_school_class(class_id: str, user_id: str) -> bool:
    """Delete a class that belongs to the authenticated user's school."""
    school = await get_school_by_user_id(user_id)
    if not school:
        return False

    school_class = await db.prisma.schoolclass.find_unique(where={"id": class_id})
    if not school_class or school_class.schoolId != school.id:
        return False

    await db.prisma.schoolclass.delete(where={"id": class_id})
    return True
