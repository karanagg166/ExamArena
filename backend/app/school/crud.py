import app.core.database as db
from app.school.schemas import SchoolCreateRequest, SchoolResponse, SchoolUpdateRequest


async def create_school(school_data: SchoolCreateRequest, user_id: str) -> SchoolResponse:
    """Create a school owned by the authenticated user."""
    data_dict = school_data.model_dump()
    data_dict["createdBy"] = user_id

    school = await db.prisma.school.create(
        data=data_dict  # type: ignore
    )
    return SchoolResponse.model_validate(school)


async def get_school_by_user_id(user_id: str) -> SchoolResponse | None:
    """Get a school by creator user ID."""
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
        where={"id": school_id},
        data=update_dict  # type: ignore
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


async def get_all_schools() -> list[SchoolResponse]:
    """Get all schools."""
    schools = await db.prisma.school.find_many()
    return [SchoolResponse.model_validate(school) for school in schools]


async def get_school_by_name(name: str) -> SchoolResponse | None:
    """Get a school by exact name."""
    school = await db.prisma.school.find_first(where={"name": name})
    return SchoolResponse.model_validate(school) if school else None


async def get_school_by_code(code: str) -> SchoolResponse | None:
    """Get a school by join code."""
    school = await db.prisma.school.find_unique(where={"schoolCode": code})
    return SchoolResponse.model_validate(school) if school else None
