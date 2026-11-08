"""Current database grants for private school records and class resources."""

from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Principal, Role, SchoolClass, Teacher, TeacherClass, User
from app.users.schemas import UserResponse


@dataclass(frozen=True)
class SchoolAccess:
    school_id: str
    # None means all classes in this school; an empty tuple grants no classes.
    class_ids: tuple[str, ...] | None

    def permits(self, school_id: str, class_id: str) -> bool:
        return self.school_id == school_id and (
            self.class_ids is None or class_id in self.class_ids
        )


async def resolve_staff_access(
    user: UserResponse, session: AsyncSession
) -> SchoolAccess:
    """Resolve live assignments, never token claims or cached ORM relationships."""
    row = (
        await session.execute(
            select(User.role, Teacher.id, Teacher.schoolId)
            .join(Teacher, Teacher.userId == User.id)
            .where(User.id == user.id)
        )
    ).one_or_none()
    if (
        row is None
        or row.role != user.role
        or row.role not in (Role.TEACHER, Role.PRINCIPAL, Role.ADMIN)
        or not row.schoolId
    ):
        raise HTTPException(403, "An active school staff affiliation is required.")
    if row.role == Role.PRINCIPAL:
        principal_school = await session.scalar(
            select(Principal.schoolId).where(Principal.teacherId == row.id)
        )
        if principal_school != row.schoolId:
            raise HTTPException(403, "Principal school authority is required.")
    if row.role in (Role.PRINCIPAL, Role.ADMIN):
        return SchoolAccess(row.schoolId, None)

    assigned = select(TeacherClass.classId).where(TeacherClass.teacherId == row.id)
    class_ids = (
        await session.scalars(
            select(SchoolClass.id).where(
                SchoolClass.schoolId == row.schoolId,
                or_(SchoolClass.teacherId == row.id, SchoolClass.id.in_(assigned)),
            )
        )
    ).all()
    return SchoolAccess(row.schoolId, tuple(class_ids))


async def require_staff_class(
    user: UserResponse, school_id: str, class_id: str, session: AsyncSession
) -> None:
    access = await resolve_staff_access(user, session)
    if not access.permits(school_id, class_id):
        raise HTTPException(403, "Access requires authority for this school and class.")
