from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import app.core.database as db
from app.core.models import Student, User
from app.students.schemas import (
    StudentCreate,
    StudentFilterParams,
    StudentListItemResponse,
    StudentUpdate,
)


async def get_student_by_user_id(user_id: str, session: AsyncSession | None = None):
    """Get student by user ID with user data"""

    async def _do_get(s: AsyncSession):
        stmt = (
            select(Student)
            .where(Student.userId == user_id)
            .options(
                selectinload(Student.user),
                selectinload(Student.schoolClass),
                selectinload(Student.school),
            )
        )
        student = (await s.execute(stmt)).scalar_one_or_none()
        if student:
            if getattr(student, "schoolClass", None):
                student.className = student.schoolClass.name
            if getattr(student, "school", None):
                student.schoolName = student.school.name
        return student

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def get_student_by_id(student_id: str, session: AsyncSession | None = None):
    """Get student by primary ID with user data"""

    async def _do_get(s: AsyncSession):
        stmt = (
            select(Student)
            .where(Student.id == student_id)
            .options(
                selectinload(Student.user),
                selectinload(Student.schoolClass),
                selectinload(Student.school),
            )
        )
        student = (await s.execute(stmt)).scalar_one_or_none()
        if student:
            if getattr(student, "schoolClass", None):
                student.className = student.schoolClass.name
            if getattr(student, "school", None):
                student.schoolName = student.school.name
        return student

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def get_students(
    filters: StudentFilterParams, session: AsyncSession | None = None
) -> list[StudentListItemResponse]:
    """Get all students with optional filters."""

    async def _do_get_all(s: AsyncSession):
        stmt = select(Student).options(
            selectinload(Student.user),
            selectinload(Student.schoolClass),
            selectinload(Student.school),
        )

        if filters.scopeSchoolId:
            stmt = stmt.where(Student.schoolId == filters.scopeSchoolId)
        if filters.scopeClassId:
            stmt = stmt.where(Student.classId == filters.scopeClassId)
        if filters.rollNo:
            stmt = stmt.where(Student.rollNo.ilike(f"%{filters.rollNo}%"))

        students = (await s.execute(stmt)).scalars().all()

        results: list[StudentListItemResponse] = []
        for student in students:
            user = getattr(student, "user", None)
            name = getattr(user, "name", "") or ""
            email = getattr(user, "email", "") or ""
            phone_no = getattr(user, "phoneNo", None)
            school_class = getattr(student, "schoolClass", None)
            school = getattr(student, "school", None)
            class_name = getattr(school_class, "name", None)
            class_year = (getattr(school_class, "year", "") or "").lower()
            class_section = (getattr(school_class, "section", "") or "").lower()
            school_name = (getattr(school, "name", "") or "").lower()
            school_code = (getattr(school, "schoolCode", "") or "").lower()

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
                    className=class_name,
                    schoolId=student.schoolId,
                    schoolName=getattr(school, "name", None),
                    name=name,
                    email=email,
                    phoneNo=phone_no,
                )
            )

        return results

    if session:
        return await _do_get_all(session)
    async with db.get_session() as s:
        return await _do_get_all(s)


async def get_students_by_class_id(class_id: str, session: AsyncSession | None = None):
    """Get all students for a given class ID"""

    async def _do_get(s: AsyncSession):
        stmt = (
            select(Student)
            .where(Student.classId == class_id)
            .options(selectinload(Student.user), selectinload(Student.schoolClass))
        )
        students = (await s.execute(stmt)).scalars().all()
        for st in students:
            if getattr(st, "schoolClass", None):
                st.className = st.schoolClass.name
        return students

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def create_student(
    student_data: StudentCreate, session: AsyncSession | None = None
):
    """Create student record"""
    computed_parent_name = (
        student_data.parentName
        or student_data.fatherName
        or student_data.motherName
        or student_data.guardianName
        or ""
    )
    computed_parent_email = (
        student_data.parentEmail
        or student_data.fatherEmail
        or student_data.motherEmail
        or student_data.guardianEmail
        or ""
    )

    async def _do_create(s: AsyncSession):
        student = Student(
            userId=student_data.userId,
            rollNo=student_data.rollNo,
            parentName=computed_parent_name,
            parentEmail=computed_parent_email,
            fatherName=student_data.fatherName,
            fatherEmail=student_data.fatherEmail,
            fatherPhoneNo=student_data.fatherPhoneNo,
            motherName=student_data.motherName,
            motherEmail=student_data.motherEmail,
            motherPhoneNo=student_data.motherPhoneNo,
            guardianName=student_data.guardianName,
            guardianRelation=student_data.guardianRelation,
            guardianEmail=student_data.guardianEmail,
            guardianPhoneNo=student_data.guardianPhoneNo,
            schoolId=student_data.schoolId,
            classId=student_data.classId,
        )
        s.add(student)
        await s.commit()
        await s.refresh(student)

        stmt = (
            select(Student)
            .where(Student.userId == student_data.userId)
            .options(selectinload(Student.user), selectinload(Student.schoolClass))
        )
        res = (await s.execute(stmt)).scalar_one_or_none()
        if res and getattr(res, "schoolClass", None):
            res.className = res.schoolClass.name
        return res

    if session:
        return await _do_create(session)
    async with db.get_session() as s:
        return await _do_create(s)


async def update_student(
    user_id: str, student_data: StudentUpdate, session: AsyncSession | None = None
):
    """Update student record and associated user data"""
    update_dict = student_data.model_dump(exclude_unset=True)
    user_data = update_dict.pop("user", None)

    # Roll number, schoolId, and classId are strictly immutable once assigned by school administration
    update_dict.pop("rollNo", None)
    update_dict.pop("schoolId", None)
    update_dict.pop("classId", None)

    async def _do_update(s: AsyncSession):
        if user_data:
            user_stmt = select(User).where(User.id == user_id)
            user = (await s.execute(user_stmt)).scalar_one_or_none()
            if user:
                for k, v in user_data.items():
                    setattr(user, k, v)

        if update_dict:
            student_stmt = select(Student).where(Student.userId == user_id)
            student = (await s.execute(student_stmt)).scalar_one_or_none()
            if student:
                for k, v in update_dict.items():
                    setattr(student, k, v)

        await s.commit()

        stmt = (
            select(Student)
            .where(Student.userId == user_id)
            .options(selectinload(Student.user), selectinload(Student.schoolClass))
        )
        res = (await s.execute(stmt)).scalar_one_or_none()
        if res and getattr(res, "schoolClass", None):
            res.className = res.schoolClass.name
        return res

    if session:
        return await _do_update(session)
    async with db.get_session() as s:
        return await _do_update(s)


async def delete_student(user_id: str, session: AsyncSession | None = None):
    """Delete student record"""

    async def _do_delete(s: AsyncSession):
        stmt = select(Student).where(Student.userId == user_id)
        student = (await s.execute(stmt)).scalar_one_or_none()
        if student:
            await s.delete(student)
            await s.commit()
            return student
        return None

    if session:
        return await _do_delete(session)
    async with db.get_session() as s:
        return await _do_delete(s)
