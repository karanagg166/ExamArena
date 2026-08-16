from datetime import UTC, datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import app.core.database as db
from app.core.models import (
    ClassJoinRequest,
    JoinRequestStatus,
    Notification,
    SchoolClass,
    Student,
)
from app.join_requests.schemas import JoinRequestResponse


def _response(request: ClassJoinRequest) -> JoinRequestResponse:
    user = request.user
    school_class = request.schoolClass
    class_name = school_class.name if school_class else ""
    school_id = school_class.schoolId if school_class else None
    return JoinRequestResponse(
        id=request.id,
        studentUserId=request.studentUserId,
        classId=request.classId,
        className=class_name,
        schoolId=school_id,
        status=request.status.value
        if isinstance(request.status, JoinRequestStatus)
        else str(request.status),
        requestedAt=request.requestedAt,
        decidedAt=request.decidedAt,
        studentName=user.name if user else "",
        studentEmail=user.email if user else "",
    )


REQUEST_OPTIONS = [
    selectinload(ClassJoinRequest.user),
    selectinload(ClassJoinRequest.schoolClass),
]


async def get_class_by_join_code(
    join_code: str, session: AsyncSession | None = None
) -> SchoolClass | None:
    async def _get(s: AsyncSession):
        return await s.scalar(
            select(SchoolClass).where(
                func.upper(SchoolClass.joinCode) == join_code.strip().upper()
            )
        )

    if session:
        return await _get(session)
    async with db.get_session() as session:
        return await _get(session)


async def create_or_reopen_join_request(
    student_user_id: str,
    school_class: SchoolClass,
    session: AsyncSession | None = None,
) -> JoinRequestResponse:
    """Create a request, allowing a previously rejected student to reapply."""

    async def _create(s: AsyncSession):
        existing_student = await s.scalar(
            select(Student).where(Student.userId == student_user_id)
        )
        if existing_student:
            raise ValueError(
                "You already have an active class and school enrollment. You cannot join another class until you leave your current class."
            )

        existing = await s.scalar(
            select(ClassJoinRequest)
            .where(
                ClassJoinRequest.studentUserId == student_user_id,
                ClassJoinRequest.classId == school_class.id,
            )
            .options(*REQUEST_OPTIONS)
        )
        if existing:
            if existing.status == JoinRequestStatus.PENDING:
                raise ValueError("Join request already pending for this class.")
            if existing.status == JoinRequestStatus.APPROVED:
                raise ValueError("You are already enrolled in this class.")
            existing.status = JoinRequestStatus.PENDING
            existing.requestedAt = datetime.now(UTC)
            existing.decidedAt = None
            existing.decidedBy = None
            await s.commit()
            await s.refresh(existing, attribute_names=["user", "schoolClass"])
            return _response(existing)

        request = ClassJoinRequest(
            studentUserId=student_user_id,
            classId=school_class.id,
            status=JoinRequestStatus.PENDING,
        )
        s.add(request)
        await s.commit()
        result = await s.scalar(
            select(ClassJoinRequest)
            .where(ClassJoinRequest.id == request.id)
            .options(*REQUEST_OPTIONS)
        )
        assert result is not None
        return _response(result)

    if session:
        return await _create(session)
    async with db.get_session() as session:
        return await _create(session)


async def get_join_requests_for_user(
    student_user_id: str, session: AsyncSession | None = None
) -> list[JoinRequestResponse]:
    async def _get(s: AsyncSession):
        requests = (
            (
                await s.execute(
                    select(ClassJoinRequest)
                    .where(ClassJoinRequest.studentUserId == student_user_id)
                    .options(*REQUEST_OPTIONS)
                    .order_by(ClassJoinRequest.requestedAt.desc())
                )
            )
            .scalars()
            .all()
        )
        return [_response(request) for request in requests]

    if session:
        return await _get(session)
    async with db.get_session() as session:
        return await _get(session)


async def get_join_requests_for_school(
    school_id: str,
    request_status: JoinRequestStatus | None = None,
    session: AsyncSession | None = None,
) -> list[JoinRequestResponse]:
    """Get all student class join requests across all classes of a school."""

    async def _get(s: AsyncSession):
        stmt = (
            select(ClassJoinRequest)
            .join(SchoolClass, ClassJoinRequest.classId == SchoolClass.id)
            .where(SchoolClass.schoolId == school_id)
            .options(*REQUEST_OPTIONS)
            .order_by(ClassJoinRequest.requestedAt.desc())
        )
        if request_status:
            stmt = stmt.where(ClassJoinRequest.status == request_status)
        requests = (await s.execute(stmt)).scalars().all()
        return [_response(request) for request in requests]

    if session:
        return await _get(session)
    async with db.get_session() as session:
        return await _get(session)


async def get_join_requests_for_class(
    class_id: str,
    request_status: JoinRequestStatus = JoinRequestStatus.PENDING,
    session: AsyncSession | None = None,
) -> list[JoinRequestResponse]:
    async def _get(s: AsyncSession):
        requests = (
            (
                await s.execute(
                    select(ClassJoinRequest)
                    .where(
                        ClassJoinRequest.classId == class_id,
                        ClassJoinRequest.status == request_status,
                    )
                    .options(*REQUEST_OPTIONS)
                    .order_by(ClassJoinRequest.requestedAt.asc())
                )
            )
            .scalars()
            .all()
        )
        return [_response(request) for request in requests]

    if session:
        return await _get(session)
    async with db.get_session() as session:
        return await _get(session)


async def get_join_request_by_id(
    request_id: str, session: AsyncSession | None = None
) -> ClassJoinRequest | None:
    async def _get(s: AsyncSession):
        return await s.scalar(
            select(ClassJoinRequest)
            .where(ClassJoinRequest.id == request_id)
            .options(*REQUEST_OPTIONS)
        )

    if session:
        return await _get(session)
    async with db.get_session() as session:
        return await _get(session)


async def decide_join_request(
    request_id: str,
    decision: JoinRequestStatus,
    decided_by_user_id: str,
    roll_no: str | None = None,
    auto_roll_no: bool = True,
    session: AsyncSession | None = None,
) -> JoinRequestResponse | None:
    """Apply a decision and allocate a per-class monotonic or custom roll number."""

    async def _decide(s: AsyncSession):
        async with s.begin():
            request = await s.scalar(
                select(ClassJoinRequest)
                .where(ClassJoinRequest.id == request_id)
                .options(*REQUEST_OPTIONS)
                .with_for_update()
            )
            if not request or request.status != JoinRequestStatus.PENDING:
                return None

            school_class = await s.scalar(
                select(SchoolClass)
                .where(SchoolClass.id == request.classId)
                .with_for_update()
            )
            if not school_class:
                return None

            request.status = decision
            request.decidedAt = datetime.now(UTC)
            request.decidedBy = decided_by_user_id

            if decision == JoinRequestStatus.APPROVED:
                existing_student = await s.scalar(
                    select(Student.id).where(Student.userId == request.studentUserId)
                )
                if existing_student:
                    raise ValueError("Student already has an enrolled profile")

                assigned_roll_no: str
                if roll_no and roll_no.strip():
                    assigned_roll_no = roll_no.strip()
                    dup_stmt = select(Student.id).where(
                        and_(
                            Student.classId == school_class.id,
                            Student.rollNo == assigned_roll_no,
                        )
                    )
                    dup = (await s.execute(dup_stmt)).scalar_one_or_none()
                    if dup:
                        raise ValueError(
                            f"Roll number '{assigned_roll_no}' is already assigned in this class"
                        )
                else:
                    assigned_roll_no = str(school_class.nextRollNo)
                    school_class.nextRollNo += 1

                s.add(
                    Student(
                        userId=request.studentUserId,
                        rollNo=assigned_roll_no,
                        classId=school_class.id,
                        schoolId=school_class.schoolId,
                    )
                )
                message = (
                    f"Your request to join {school_class.name} was approved. "
                    f"Your roll number is {assigned_roll_no}."
                )
            else:
                message = f"Your request to join {school_class.name} was rejected."

            s.add(Notification(userId=request.studentUserId, message=message))

        result = await s.scalar(
            select(ClassJoinRequest)
            .where(ClassJoinRequest.id == request_id)
            .options(*REQUEST_OPTIONS)
        )
        assert result is not None
        return _response(result)

    if session:
        return await _decide(session)
    async with db.get_session() as session:
        return await _decide(session)
