from typing import Any, cast

import app.core.database as db
from app.school.schemas import (
    SchoolCreateRequest,
    SchoolFilterParams,
    SchoolResponse,
    SchoolUpdateRequest,
)


async def create_school(
    school_data: SchoolCreateRequest, user_id: str
) -> SchoolResponse:
    """Create a school owned by the authenticated user."""
    data_dict = school_data.model_dump()
    data_dict["createdBy"] = user_id

    school = await db.prisma.school.create(data=data_dict)  # type: ignore
    return SchoolResponse.model_validate(school)


async def get_school_by_user_id(user_id: str) -> SchoolResponse | None:
    """Get a school by creator user ID."""
    user = await db.prisma.user.find_unique(where={"id": user_id})
    if not user:
        return None

    role = getattr(user, "role", None)
    role_value = getattr(role, "value", None) or str(role)

    if role_value == "PRINCIPAL":
        teacher = await db.prisma.teacher.find_unique(where={"userId": user_id})
        if not teacher:
            return None

        principal = await db.prisma.principal.find_unique(
            where={"teacherId": teacher.id}
        )
        school_id = (
            principal.schoolId
            if principal and getattr(principal, "schoolId", None)
            else teacher.schoolId
        )
        if not school_id:
            return None

        school = await db.prisma.school.find_unique(where={"id": school_id})
        return SchoolResponse.model_validate(school) if school else None

    if role_value == "TEACHER":
        teacher = await db.prisma.teacher.find_unique(where={"userId": user_id})
        if not teacher or not teacher.schoolId:
            return None
        school = await db.prisma.school.find_unique(where={"id": teacher.schoolId})
        return SchoolResponse.model_validate(school) if school else None

    if role_value == "STUDENT":
        student = await db.prisma.student.find_unique(where={"userId": user_id})
        if not student:
            return None

        school = await db.prisma.school.find_unique(where={"id": student.schoolId})
        return SchoolResponse.model_validate(school) if school else None

    school = await db.prisma.school.find_first(where={"createdBy": user_id})
    return SchoolResponse.model_validate(school) if school else None


async def update_school(
    school_id: str, school_data: SchoolUpdateRequest
) -> SchoolResponse | None:
    """Update a school by ID."""
    update_dict = school_data.model_dump(exclude_unset=True)

    if not update_dict:
        school = await db.prisma.school.find_unique(where={"id": school_id})
        return SchoolResponse.model_validate(school) if school else None

    updated_school = await db.prisma.school.update(
        where={"id": school_id}, data=update_dict  # type: ignore
    )
    return SchoolResponse.model_validate(updated_school)


async def delete_school(school_id: str) -> SchoolResponse | None:
    """Delete a school by ID."""
    deleted_school = await db.prisma.school.delete(where={"id": school_id})
    return SchoolResponse.model_validate(deleted_school) if deleted_school else None


async def get_school_by_id(school_id: str) -> SchoolResponse | None:
    """Get a school by its database ID."""
    school = await db.prisma.school.find_unique(where={"id": school_id})
    return SchoolResponse.model_validate(school) if school else None


async def get_schools(filters: SchoolFilterParams) -> list[SchoolResponse]:
    """Get all schools with optional filters."""

    where: dict[str, object] = {}

    if filters.name:
        where["name"] = {"contains": filters.name, "mode": "insensitive"}
    if filters.city:
        where["city"] = {"contains": filters.city, "mode": "insensitive"}
    if filters.state:
        where["state"] = {"contains": filters.state, "mode": "insensitive"}
    if filters.country:
        where["country"] = {"contains": filters.country, "mode": "insensitive"}
    if filters.pincode:
        where["pincode"] = {"contains": filters.pincode, "mode": "insensitive"}
    if filters.school_code:
        where["schoolCode"] = {"contains": filters.school_code, "mode": "insensitive"}
    if filters.email:
        where["email"] = {"contains": filters.email, "mode": "insensitive"}
    if filters.website:
        where["website"] = {"contains": filters.website, "mode": "insensitive"}
    if filters.school_type:
        where["type"] = filters.school_type  # exact match — enum

    schools = await db.prisma.school.find_many(where=cast(Any, where))
    return [SchoolResponse.model_validate(school) for school in schools]


async def get_school_by_name(name: str) -> SchoolResponse | None:
    """Get a school by exact name."""
    school = await db.prisma.school.find_first(where={"name": name})
    return SchoolResponse.model_validate(school) if school else None


async def get_school_by_code(code: str) -> SchoolResponse | None:
    """Get a school by join code."""
    school = await db.prisma.school.find_unique(where={"schoolCode": code})
    return SchoolResponse.model_validate(school) if school else None
