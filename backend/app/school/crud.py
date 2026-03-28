from datetime import datetime, timezone
from app.school.schemas import SchoolCreateRequest, SchoolUpdateRequest, SchoolResponse
import app.core.database as db

async def create_school(school_data: SchoolCreateRequest, userId: str) -> SchoolResponse:
    """Create new school and return as SchoolResponse"""
    data_dict = school_data.model_dump()
    data_dict["createdBy"] = userId
    
    school = await db.prisma.school.create(
        data=data_dict # type: ignore
    )

    # Convert the Prisma object to your Pydantic Response Schema
    return SchoolResponse.model_validate(school)


async def get_school_by_user_id(user_id: str) -> SchoolResponse | None:
    """Get school by user ID"""
    school = await db.prisma.school.find_first(where={"createdBy": user_id})
    
    if not school:
        return None
        
    return SchoolResponse.model_validate(school)


async def update_school(school_id: str, school_data: SchoolUpdateRequest) -> SchoolResponse | None:
    """Update school data"""
    update_dict = school_data.model_dump(exclude_unset=True)
    
    if not update_dict:
        school = await db.prisma.school.find_unique(where={"id": school_id})
        return SchoolResponse.model_validate(school) if school else None
    
    updated_school = await db.prisma.school.update(
        where={"id": school_id},
        data=update_dict # type: ignore
    )
    
    return SchoolResponse.model_validate(updated_school)


async def delete_school(school_id: str) -> SchoolResponse | None:
    """Delete school by ID"""
    deleted_school = await db.prisma.school.delete(where={"id": school_id})
    return SchoolResponse.model_validate(deleted_school) if deleted_school else None


async def get_school_by_id(school_id: str) -> SchoolResponse | None:
    """Get school by ID"""
    school = await db.prisma.school.find_first(where={"schoolCode": school_id})
    return SchoolResponse.model_validate(school) if school else None


async def get_all_schools() -> list[SchoolResponse]:
    """Get all schools (Returns a List of SchoolResponses)"""
    schools = await db.prisma.school.find_many()
    
    # Use a list comprehension to convert every Prisma object into a Pydantic model
    return [SchoolResponse.model_validate(school) for school in schools]


async def get_school_by_name(name: str) -> SchoolResponse | None:
    """Get school by name"""
    school = await db.prisma.school.find_first(where={"name": name})
    return SchoolResponse.model_validate(school) if school else None


async def get_school_by_code(code: str) -> SchoolResponse | None:
    """Get school by code"""
    school = await db.prisma.school.find_unique(where={"schoolCode": code})
    return SchoolResponse.model_validate(school) if school else None