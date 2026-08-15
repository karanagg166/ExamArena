from datetime import UTC, datetime

from sqlalchemy import func, select
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
    return JoinRequestResponse(
        id=request.id,
        studentUserId=request.studentUserId,
        classId=request.classId,
        className=school_class.name,
        status=request.status.value
        if isinstance(request.status, JoinRequestStatus)
        else str(request.status),
        requestedAt=request.requestedAt,
        decidedAt=request.decidedAt,
        studentName=user.name,
        studentEmail=user.email,
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
            select(SchoolClass).where(SchoolClass.joinCode == join_code.strip().upper())
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
        existing = await s.scalar(
            select(ClassJoinRequest)
            .where(
                ClassJoinRequest.studentUserId == student_user_id,
                ClassJoinRequest.classId == school_class.id,
            )
            .options(*REQUEST_OPTIONS)
        )
        if existing:
            if existing.status in (
                JoinRequestStatus.PENDING,
                JoinRequestStatus.APPROVED,
            ):
                raise ValueError("A join request for this class already exists")
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
    decided_by_teacher_id: str,
    session: AsyncSession | None = None,
) -> JoinRequestResponse | None:
    """Apply a decision and atomically allocate a per-class monotonic roll number."""

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
            request.decidedBy = decided_by_teacher_id

            if decision == JoinRequestStatus.APPROVED:
                existing_student = await s.scalar(
                    select(Student.id).where(Student.userId == request.studentUserId)
                )
                if existing_student:
                    raise ValueError("Student already has an enrolled profile")

                roll_no = str(school_class.nextRollNo)
                school_class.nextRollNo += 1
                s.add(
                    Student(
                        userId=request.studentUserId,
                        rollNo=roll_no,
                        classId=school_class.id,
                        schoolId=school_class.schoolId,
                    )
                )
                message = (
                    f"Your request to join {school_class.name} was approved. "
                    f"Your roll number is {roll_no}."
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
