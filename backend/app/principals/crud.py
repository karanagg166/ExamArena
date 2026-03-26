import app.core.database as db
from app.principals.schemas import PrincipalUpdate

async def get_principal_by_teacher_id(teacher_id: str):
    """Get principal by teacherId"""
    return await db.prisma.principal.find_unique(
        where={"teacherId": teacher_id},
        include={"teacher": {"include": {"user": True}}, "school": True}
    )


async def create_principal(teacher_id: str, experience: int = 0):
    """Create principal record linked to an existing teacher"""
    return await db.prisma.principal.create(data={
        "teacherId": teacher_id,
        "experience": experience,
    })


async def update_principal(teacher_id: str, principal_data: PrincipalUpdate):
    """Update principal record"""
    update_dict = principal_data.model_dump(exclude_unset=True)
    if update_dict:
        await db.prisma.principal.update(
            where={"teacherId": teacher_id},
            data=update_dict
        )
    return await get_principal_by_teacher_id(teacher_id)


async def delete_principal(teacher_id: str):
    """Delete principal record"""
    return await db.prisma.principal.delete(where={"teacherId": teacher_id})
