import app.core.database as db
from app.principals.schemas import PrincipalUpdate
from prisma.enums import Role  # type: ignore


async def get_principal_by_teacher_id(teacher_id: str):
    """Get a principal by teacher ID."""
    return await db.prisma.principal.find_unique(
        where={"teacherId": teacher_id},
        include={"teacher": {"include": {"user": True}}, "school": True},
    )


async def create_principal(
    teacher_id: str, experience: int = 0, school_id: str | None = None
):
    """Create a principal linked to an existing teacher."""
    teacher = await db.prisma.teacher.find_unique(where={"id": teacher_id})
    if teacher:
        await db.prisma.user.update(
            where={"id": teacher.userId},
            data={"role": Role.PRINCIPAL},
        )

    await db.prisma.principal.create(
        data={
            "teacherId": teacher_id,
            "experience": experience,
            "schoolId": school_id,
        }
    )
    return await get_principal_by_teacher_id(teacher_id)


async def update_principal(teacher_id: str, principal_data: PrincipalUpdate):
    """Update a principal by teacher ID."""
    update_dict = principal_data.model_dump(exclude_unset=True)
    if update_dict:
        await db.prisma.principal.update(
            where={"teacherId": teacher_id},
            data=update_dict,
        )
    return await get_principal_by_teacher_id(teacher_id)


async def delete_principal(teacher_id: str):
    """Delete a principal by teacher ID."""
    return await db.prisma.principal.delete(where={"teacherId": teacher_id})
