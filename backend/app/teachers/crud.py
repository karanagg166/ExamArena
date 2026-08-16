import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import app.core.database as db
from app.core.models import Qualification, Subject, Teacher, User
from app.school.crud import get_school_by_id
from app.teachers.schemas import (
    TeacherCreate,
    TeacherFilterParams,
    TeacherListItemResponse,
    TeacherUpdate,
)


async def get_teacher_by_user_id(user_id: str, session: AsyncSession | None = None):
    """Get teacher by user ID with user data and auto-cascade school affiliation if needed"""
    from app.core.models import TeacherClass

    async def _do_get(s: AsyncSession):
        stmt = (
            select(Teacher)
            .where(Teacher.userId == user_id)
            .options(
                selectinload(Teacher.user),
                selectinload(Teacher.classes).selectinload(TeacherClass.schoolClass),
            )
        )
        teacher = (await s.execute(stmt)).scalar_one_or_none()
        if teacher and not teacher.schoolId and teacher.classes:
            for tc in teacher.classes:
                if tc.schoolClass and tc.schoolClass.schoolId:
                    teacher.schoolId = tc.schoolClass.schoolId
                    await s.commit()
                    await s.refresh(teacher)
                    break
        return teacher

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def get_teacher_by_id(teacher_id: str, session: AsyncSession | None = None):
    """Get teacher by primary ID with user data and auto-cascade school affiliation if needed"""
    from app.core.models import TeacherClass

    async def _do_get(s: AsyncSession):
        stmt = (
            select(Teacher)
            .where(Teacher.id == teacher_id)
            .options(
                selectinload(Teacher.user),
                selectinload(Teacher.classes).selectinload(TeacherClass.schoolClass),
            )
        )
        teacher = (await s.execute(stmt)).scalar_one_or_none()
        if teacher and not teacher.schoolId and teacher.classes:
            for tc in teacher.classes:
                if tc.schoolClass and tc.schoolClass.schoolId:
                    teacher.schoolId = tc.schoolClass.schoolId
                    await s.commit()
                    await s.refresh(teacher)
                    break
        return teacher

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


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


async def get_teachers(
    filters: TeacherFilterParams, session: AsyncSession | None = None
) -> list[TeacherListItemResponse]:
    """Get teachers with filters"""

    async def _do_get_all(s: AsyncSession):
        stmt = select(Teacher).options(selectinload(Teacher.user))

        if filters.department:
            stmt = stmt.where(Teacher.department.ilike(f"%{filters.department}%"))

        if filters.min_experience is not None:
            stmt = stmt.where(Teacher.experience >= filters.min_experience)
        if filters.max_experience is not None:
            stmt = stmt.where(Teacher.experience <= filters.max_experience)

        teachers = (await s.execute(stmt)).scalars().all()

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

    if session:
        return await _do_get_all(session)
    async with db.get_session() as s:
        return await _do_get_all(s)


async def create_teacher(
    teacher_data: TeacherCreate, session: AsyncSession | None = None
):
    """Create teacher record — serialize qualifications/subjects lists to JSON strings"""

    async def _do_create(s: AsyncSession):
        teacher = Teacher(
            userId=teacher_data.userId,
            qualification=json.dumps(teacher_data.qualifications),
            experience=teacher_data.experience,
            department=teacher_data.department,
            subjects=json.dumps(teacher_data.subjects),
        )
        s.add(teacher)
        await s.commit()
        await s.refresh(teacher)

        stmt = (
            select(Teacher)
            .where(Teacher.userId == teacher_data.userId)
            .options(selectinload(Teacher.user))
        )
        return (await s.execute(stmt)).scalar_one_or_none()

    if session:
        return await _do_create(session)
    async with db.get_session() as s:
        return await _do_create(s)


async def update_teacher(
    user_id: str, teacher_data: TeacherUpdate, session: AsyncSession | None = None
):
    """Update teacher record and associated user data"""
    update_dict = teacher_data.model_dump(exclude_unset=True)
    user_data = update_dict.pop("user", None)

    teacher_fields = {}
    if "qualifications" in update_dict:
        teacher_fields["qualification"] = json.dumps(update_dict.pop("qualifications"))
    if "subjects" in update_dict:
        teacher_fields["subjects"] = json.dumps(update_dict.pop("subjects"))

    teacher_fields.update(update_dict)

    async def _do_update(s: AsyncSession):
        if user_data:
            user_stmt = select(User).where(User.id == user_id)
            user = (await s.execute(user_stmt)).scalar_one_or_none()
            if user:
                for k, v in user_data.items():
                    setattr(user, k, v)

        if teacher_fields:
            teacher_stmt = select(Teacher).where(Teacher.userId == user_id)
            teacher = (await s.execute(teacher_stmt)).scalar_one_or_none()
            if teacher:
                for k, v in teacher_fields.items():
                    setattr(teacher, k, v)

        await s.commit()

        stmt = (
            select(Teacher)
            .where(Teacher.userId == user_id)
            .options(selectinload(Teacher.user))
        )
        return (await s.execute(stmt)).scalar_one_or_none()

    if session:
        return await _do_update(session)
    async with db.get_session() as s:
        return await _do_update(s)


async def delete_teacher(user_id: str, session: AsyncSession | None = None):
    """Delete teacher record"""

    async def _do_delete(s: AsyncSession):
        stmt = select(Teacher).where(Teacher.userId == user_id)
        teacher = (await s.execute(stmt)).scalar_one_or_none()
        if teacher:
            await s.delete(teacher)
            await s.commit()
            return teacher
        return None

    if session:
        return await _do_delete(session)
    async with db.get_session() as s:
        return await _do_delete(s)


async def get_all_qualifications():
    return [q.value for q in Qualification]


async def get_all_subjects():
    return [s.value for s in Subject]


async def join_school(
    user_id: str, school_id: str, session: AsyncSession | None = None
):
    """Assign the teacher profile to a school by school ID."""
    school = await get_school_by_id(school_id, session=session)
    if not school:
        return False

    async def _do_join(s: AsyncSession):
        teacher_stmt = select(Teacher).where(Teacher.userId == user_id)
        teacher = (await s.execute(teacher_stmt)).scalar_one_or_none()
        if not teacher:
            return None
        teacher.schoolId = school_id
        await s.commit()

        stmt = (
            select(Teacher)
            .where(Teacher.userId == user_id)
            .options(selectinload(Teacher.user))
        )
        return (await s.execute(stmt)).scalar_one_or_none()

    if session:
        return await _do_join(session)
    async with db.get_session() as s:
        return await _do_join(s)
