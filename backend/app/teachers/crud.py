import json

from prisma.enums import Qualification, Subject  # type: ignore

import app.core.database as db
from app.teachers.schemas import TeacherCreate, TeacherUpdate


async def get_teacher_by_user_id(user_id: str):
    """Get teacher by user ID with user data"""
    return await db.prisma.teacher.find_unique(
        where={"userId": user_id}, include={"user": True}
    )


async def get_teacher_by_id(teacher_id: str):
    """Get teacher by primary ID with user data"""
    return await db.prisma.teacher.find_unique(
        where={"id": teacher_id}, include={"user": True}
    )


async def create_teacher(teacher_data: TeacherCreate):
    """Create teacher record — serialize qualifications/subjects lists to JSON strings"""
    await db.prisma.teacher.create(
        data={
            "userId": teacher_data.userId,
            "qualification": json.dumps(teacher_data.qualifications),
            "experience": teacher_data.experience,
            "department": teacher_data.department,
            "subjects": json.dumps(teacher_data.subjects),
        }
    )
    # Re-fetch with user relation included for the response
    return await get_teacher_by_user_id(teacher_data.userId)


async def update_teacher(user_id: str, teacher_data: TeacherUpdate):
    """Update teacher record and associated user data"""
    update_dict = teacher_data.model_dump(exclude_unset=True)

    user_data = update_dict.pop("user", None)

    if user_data:
        await db.prisma.user.update(where={"id": user_id}, data=user_data)

    # Serialize list fields to JSON strings for DB storage
    teacher_fields = {}
    if "qualifications" in update_dict:
        teacher_fields["qualification"] = json.dumps(update_dict.pop("qualifications"))
    if "subjects" in update_dict:
        teacher_fields["subjects"] = json.dumps(update_dict.pop("subjects"))

    # Remaining scalar fields (experience, department)
    teacher_fields.update(update_dict)

    if teacher_fields:
        await db.prisma.teacher.update(where={"userId": user_id}, data=teacher_fields)

    return await get_teacher_by_user_id(user_id)


async def delete_teacher(user_id: str):
    """Delete teacher record"""
    return await db.prisma.teacher.delete(where={"userId": user_id})


async def get_all_qualifications():
    return [q.value for q in Qualification]


async def get_all_subjects():
    return [s.value for s in Subject]
