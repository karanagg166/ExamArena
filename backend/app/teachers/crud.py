import json
from typing import Any, cast

from prisma.enums import Qualification, Subject  # type: ignore

import app.core.database as db
from app.school.crud import get_school_by_id
from app.teachers.schemas import (
    TeacherCreate,
    TeacherFilterParams,
    TeacherListItemResponse,
    TeacherUpdate,
)


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


def _parse_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return [str(item).strip() for item in parsed if str(item).strip()]
    except Exception:
        return [item.strip() for item in value.split(",") if item.strip()]


def _contains_ci(source: str | None, target: str | None) -> bool:
    if not target:
        return True
    return target.lower() in (source or "").lower()


async def get_teachers(filters: TeacherFilterParams) -> list[TeacherListItemResponse]:
    where: dict[str, object] = {}

    if filters.department:
        where["department"] = {
            "contains": filters.department,
            "mode": "insensitive",
        }

    experience_range: dict[str, int] = {}
    if filters.min_experience is not None:
        experience_range["gte"] = filters.min_experience
    if filters.max_experience is not None:
        experience_range["lte"] = filters.max_experience
    if experience_range:
        where["experience"] = experience_range

    teachers = await db.prisma.teacher.find_many(
        where=cast(Any, where),
        include={"user": True},
    )

    results: list[TeacherListItemResponse] = []
    for teacher in teachers:
        user = getattr(teacher, "user", None)
        qualifications = _parse_json_list(getattr(teacher, "qualification", None))
        subjects = _parse_json_list(getattr(teacher, "subjects", None))

        if not _contains_ci(getattr(user, "name", None), filters.name):
            continue
        if not _contains_ci(getattr(user, "email", None), filters.email):
            continue
        if not _contains_ci(getattr(user, "phoneNo", None), filters.phone_no):
            continue
        if filters.subject and not any(
            _contains_ci(subject, filters.subject) for subject in subjects
        ):
            continue
        if filters.qualification and not any(
            _contains_ci(qualification, filters.qualification)
            for qualification in qualifications
        ):
            continue

        results.append(
            TeacherListItemResponse(
                id=teacher.id,
                name=getattr(user, "name", "") or "",
                email=getattr(user, "email", "") or "",
                phoneNo=getattr(user, "phoneNo", "") or "",
                experience=getattr(teacher, "experience", 0) or 0,
                qualifications=qualifications,
                department=getattr(teacher, "department", "") or "",
                subjects=subjects,
            )
        )

    return results


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
        await db.prisma.teacher.update(
            where={"userId": user_id},
            data=cast(Any, teacher_fields),
        )

    return await get_teacher_by_user_id(user_id)


async def delete_teacher(user_id: str):
    """Delete teacher record"""
    return await db.prisma.teacher.delete(where={"userId": user_id})


async def get_all_qualifications():
    return [q.value for q in Qualification]


async def get_all_subjects():
    return [s.value for s in Subject]


async def join_school(user_id: str, school_id: str):
    """Assign the teacher profile to a school by school ID."""
    teacher = await get_teacher_by_user_id(user_id)
    if not teacher:
        return None

    school = await get_school_by_id(school_id)
    if not school:
        return False

    await db.prisma.teacher.update(
        where={"userId": user_id},
        data=cast(Any, {"schoolId": school_id}),
    )
    return await get_teacher_by_user_id(user_id)
