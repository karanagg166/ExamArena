from typing import Any, cast

import app.core.database as db
from app.students.schemas import (
    StudentCreate,
    StudentFilterParams,
    StudentListItemResponse,
    StudentUpdate,
)


async def get_student_by_user_id(user_id: str):
    """Get student by user ID with user data"""
    return await db.prisma.student.find_unique(
        where={"userId": user_id}, include={"user": True}
    )


async def get_student_by_id(student_id: str):
    """Get student by primary ID with user data"""
    return await db.prisma.student.find_unique(
        where={"id": student_id}, include={"user": True}
    )


async def get_students(filters: StudentFilterParams) -> list[StudentListItemResponse]:
    """Get all students with optional filters."""
    where: dict[str, object] = {}

    if filters.scopeSchoolId:
        where["schoolId"] = filters.scopeSchoolId
    if filters.scopeClassId:
        where["classId"] = filters.scopeClassId
    if filters.rollNo:
        where["rollNo"] = {"contains": filters.rollNo, "mode": "insensitive"}

    students = await db.prisma.student.find_many(
        where=cast(Any, where),
        include={"user": True, "schoolClass": True, "school": True},
    )

    results: list[StudentListItemResponse] = []
    for student in students:
        user = getattr(student, "user", None)
        name = getattr(user, "name", "") or ""
        email = getattr(user, "email", "") or ""
        phone_no = getattr(user, "phoneNo", None)
        school_class = getattr(student, "schoolClass", None)
        school = getattr(student, "school", None)
        class_year = (getattr(school_class, "year", "") or "").lower()
        class_section = (getattr(school_class, "section", "") or "").lower()
        school_name = (getattr(school, "name", "") or "").lower()
        school_code = (getattr(school, "schoolCode", "") or "").lower()

        # Apply name / email filters in Python (case-insensitive)
        if filters.name and filters.name.lower() not in name.lower():
            continue
        if filters.email and filters.email.lower() not in email.lower():
            continue
        if filters.classYear and filters.classYear.lower() not in class_year:
            continue
        if filters.section and filters.section.lower() not in class_section:
            continue
        if filters.schoolName and filters.schoolName.lower() not in school_name:
            continue
        if filters.schoolCode and filters.schoolCode.lower() not in school_code:
            continue

        results.append(
            StudentListItemResponse(
                id=student.id,
                userId=student.userId,
                rollNo=student.rollNo,
                classId=student.classId,
                schoolId=student.schoolId,
                name=name,
                email=email,
                phoneNo=phone_no,
            )
        )

    return results


async def get_students_by_class_id(class_id: str):
    """Get all students for a given class ID"""
    return await db.prisma.student.find_many(
        where={"classId": class_id}, include={"user": True}
    )


async def create_student(student_data: StudentCreate):
    """Create student record"""
    await db.prisma.student.create(
        data=cast(
            Any,
            {
                "userId": student_data.userId,
                "rollNo": student_data.rollNo,
                "parentName": student_data.parentName,
                "parentEmail": student_data.parentEmail,
                "schoolId": student_data.schoolId,
                "classId": student_data.classId,
            },
        )
    )
    return await get_student_by_user_id(student_data.userId)


async def update_student(user_id: str, student_data: StudentUpdate):
    """Update student record and associated user data"""
    update_dict = student_data.model_dump(exclude_unset=True)

    # Extract user data if present
    user_data = update_dict.pop("user", None)

    # Update user data if provided
    if user_data:
        await db.prisma.user.update(where={"id": user_id}, data=user_data)

    # Update student data if any student-specific fields are provided
    if update_dict:
        await db.prisma.student.update(
            where={"userId": user_id},
            data=cast(Any, update_dict),
        )

    return await get_student_by_user_id(user_id)


async def delete_student(user_id: str):
    """Delete student record"""
    return await db.prisma.student.delete(where={"userId": user_id})
