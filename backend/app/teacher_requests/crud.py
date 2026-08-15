from datetime import UTC, datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import app.core.database as db
from app.core.models import (
    JoinRequestStatus,
    SchoolClass,
    Subject,
    Teacher,
    TeacherClass,
    TeacherClassJoinRequest,
)
from app.teacher_requests.schemas import (
    TeacherClassJoinRequestCreate,
    TeacherClassJoinRequestResponse,
)


def _to_response(req: TeacherClassJoinRequest) -> TeacherClassJoinRequestResponse:
    teacher_name = "Unknown Teacher"
    teacher_email = ""
    if req.teacher and hasattr(req.teacher, "user") and req.teacher.user:
        teacher_name = req.teacher.user.name or ""
        teacher_email = req.teacher.user.email or ""

    class_name = ""
    school_id = ""
    if req.schoolClass:
        class_name = f"{req.schoolClass.name} {req.schoolClass.section}".strip()
        school_id = req.schoolClass.schoolId or ""

    return TeacherClassJoinRequestResponse(
        id=req.id,
        teacherId=req.teacherId,
        teacherName=teacher_name,
        teacherEmail=teacher_email,
        classId=req.classId,
        className=class_name,
        schoolId=school_id,
        subject=(
            req.subject.value
            if hasattr(req.subject, "value")
            else (str(req.subject) if req.subject else None)
        ),
        status=(req.status.value if hasattr(req.status, "value") else str(req.status)),
        requestedAt=req.requestedAt,
        decidedAt=req.decidedAt,
        decidedBy=req.decidedBy,
    )


async def create_teacher_class_request(
    teacher_id: str,
    payload: TeacherClassJoinRequestCreate,
    session: AsyncSession | None = None,
) -> TeacherClassJoinRequestResponse:
    """Create a pending request for a teacher to teach a class."""

    async def _do_create(s: AsyncSession):
        # 1. Verify class exists
        cls_stmt = select(SchoolClass).where(SchoolClass.id == payload.classId)
        school_class = (await s.execute(cls_stmt)).scalar_one_or_none()
        if not school_class:
            raise ValueError("Class not found")

        # 2. Check if already teaching this class
        tc_stmt = select(TeacherClass).where(
            and_(
                TeacherClass.teacherId == teacher_id,
                TeacherClass.classId == payload.classId,
            )
        )
        already_teaching = (await s.execute(tc_stmt)).scalar_one_or_none()
        if already_teaching:
            raise ValueError("You are already assigned to teach this class")

        # 3. Check existing pending request
        existing_stmt = select(TeacherClassJoinRequest).where(
            and_(
                TeacherClassJoinRequest.teacherId == teacher_id,
                TeacherClassJoinRequest.classId == payload.classId,
            )
        )
        existing = (await s.execute(existing_stmt)).scalar_one_or_none()
        if existing:
            if existing.status == JoinRequestStatus.PENDING:
                raise ValueError("A pending request to teach this class already exists")
            # If rejected previously, reopen as PENDING
            existing.status = JoinRequestStatus.PENDING
            existing.requestedAt = datetime.now(UTC)
            existing.decidedAt = None
            existing.decidedBy = None
            existing.subject = payload.subject
            await s.commit()
            await s.refresh(existing)
            # Re-fetch with relationships
            load_stmt = (
                select(TeacherClassJoinRequest)
                .where(TeacherClassJoinRequest.id == existing.id)
                .options(
                    selectinload(TeacherClassJoinRequest.teacher).selectinload(
                        Teacher.user
                    ),
                    selectinload(TeacherClassJoinRequest.schoolClass),
                )
            )
            reloaded = (await s.execute(load_stmt)).scalar_one()
            return _to_response(reloaded)

        # 4. Create new request
        req = TeacherClassJoinRequest(
            teacherId=teacher_id,
            classId=payload.classId,
            subject=payload.subject,
            status=JoinRequestStatus.PENDING,
        )
        s.add(req)
        await s.commit()
        await s.refresh(req)

        load_stmt = (
            select(TeacherClassJoinRequest)
            .where(TeacherClassJoinRequest.id == req.id)
            .options(
                selectinload(TeacherClassJoinRequest.teacher).selectinload(
                    Teacher.user
                ),
                selectinload(TeacherClassJoinRequest.schoolClass),
            )
        )
        loaded = (await s.execute(load_stmt)).scalar_one()
        return _to_response(loaded)

    if session:
        return await _do_create(session)
    async with db.get_session() as s:
        return await _do_create(s)


async def get_teacher_requests_by_school(
    school_id: str,
    status_filter: str | None = None,
    session: AsyncSession | None = None,
) -> list[TeacherClassJoinRequestResponse]:
    """Get all teacher class requests for a specific school."""

    async def _do_get(s: AsyncSession):
        stmt = (
            select(TeacherClassJoinRequest)
            .join(SchoolClass, TeacherClassJoinRequest.classId == SchoolClass.id)
            .where(SchoolClass.schoolId == school_id)
            .options(
                selectinload(TeacherClassJoinRequest.teacher).selectinload(
                    Teacher.user
                ),
                selectinload(TeacherClassJoinRequest.schoolClass),
            )
            .order_by(TeacherClassJoinRequest.requestedAt.desc())
        )
        if status_filter:
            stmt = stmt.where(TeacherClassJoinRequest.status == status_filter)

        results = (await s.execute(stmt)).scalars().all()
        return [_to_response(r) for r in results]

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def decide_teacher_request(
    request_id: str,
    decision_status: str,
    decided_by_user_name: str,
    session: AsyncSession | None = None,
) -> TeacherClassJoinRequestResponse:
    """Approve or Reject a teacher class join request."""

    async def _do_decide(s: AsyncSession):
        stmt = (
            select(TeacherClassJoinRequest)
            .where(TeacherClassJoinRequest.id == request_id)
            .options(
                selectinload(TeacherClassJoinRequest.teacher).selectinload(
                    Teacher.user
                ),
                selectinload(TeacherClassJoinRequest.schoolClass),
            )
        )
        req = (await s.execute(stmt)).scalar_one_or_none()
        if not req:
            raise ValueError("Join request not found")

        if req.status != JoinRequestStatus.PENDING:
            raise ValueError(f"Request has already been decided ({req.status})")

        new_status = (
            JoinRequestStatus.APPROVED
            if decision_status == "APPROVED"
            else JoinRequestStatus.REJECTED
        )
        req.status = new_status
        req.decidedAt = datetime.now(UTC)
        req.decidedBy = decided_by_user_name

        if new_status == JoinRequestStatus.APPROVED:
            # Check if teacher_class row exists, otherwise insert
            tc_stmt = select(TeacherClass).where(
                and_(
                    TeacherClass.teacherId == req.teacherId,
                    TeacherClass.classId == req.classId,
                )
            )
            tc = (await s.execute(tc_stmt)).scalar_one_or_none()
            if not tc:
                s.add(
                    TeacherClass(
                        teacherId=req.teacherId,
                        classId=req.classId,
                    )
                )

        await s.commit()
        await s.refresh(req)
        return _to_response(req)

    if session:
        return await _do_decide(session)
    async with db.get_session() as s:
        return await _do_decide(s)
