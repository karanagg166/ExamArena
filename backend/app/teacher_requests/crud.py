from datetime import UTC, datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import app.core.database as db
from app.core.models import (
    JoinRequestStatus,
    Notification,
    School,
    SchoolClass,
    Subject,
    Teacher,
    TeacherClass,
    TeacherClassJoinRequest,
    TeacherSchoolJoinRequest,
)
from app.teacher_requests.schemas import (
    TeacherAssignClassesResponse,
    TeacherClassJoinRequestCreate,
    TeacherClassJoinRequestResponse,
    TeacherSchoolJoinRequestResponse,
)


def normalize_subject(subject_val: str | Subject | None) -> Subject | None:
    if not subject_val:
        return None
    if isinstance(subject_val, Subject):
        return subject_val
    cleaned = str(subject_val).strip().upper().replace(" ", "_")
    if cleaned in ("MATHS", "MATHEMATICS", "MATH"):
        return Subject.MATHS
    if cleaned in ("SCIENCE", "PHYSICS", "CHEMISTRY", "BIOLOGY"):
        return Subject.SCIENCE
    if cleaned in ("HISTORY", "SOCIAL_STUDIES", "GEOGRAPHY"):
        return Subject.HISTORY
    if cleaned in ("LITERATURE", "ENGLISH"):
        return Subject.LITERATURE
    if cleaned == "ART":
        return Subject.ART
    if cleaned == "MUSIC":
        return Subject.MUSIC
    if cleaned in ("PHYSICAL_EDUCATION", "PE", "SPORTS"):
        return Subject.PHYSICAL_EDUCATION
    try:
        return Subject(cleaned)
    except Exception:
        return Subject.MATHS


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


def _to_school_request_response(
    req: TeacherSchoolJoinRequest,
) -> TeacherSchoolJoinRequestResponse:
    teacher_name = "Unknown Teacher"
    teacher_email = ""
    teacher_department = None
    if req.teacher:
        teacher_department = req.teacher.department
        if hasattr(req.teacher, "user") and req.teacher.user:
            teacher_name = req.teacher.user.name or ""
            teacher_email = req.teacher.user.email or ""

    school_name = "Unknown School"
    if req.school:
        school_name = req.school.name

    return TeacherSchoolJoinRequestResponse(
        id=req.id,
        teacherId=req.teacherId,
        teacherName=teacher_name,
        teacherEmail=teacher_email,
        teacherDepartment=teacher_department,
        schoolId=req.schoolId,
        schoolName=school_name,
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

        # Verify teacher has an approved school membership
        t_stmt = select(Teacher).where(Teacher.id == teacher_id)
        teacher = (await s.execute(t_stmt)).scalar_one_or_none()
        if not teacher:
            raise ValueError("Teacher profile not found")
        if not teacher.schoolId:
            raise ValueError(
                "You must first join and be approved by a School before you can request to teach a class."
            )
        if teacher.schoolId != school_class.schoolId:
            raise ValueError(
                "You can only request to teach classes within your approved school."
            )

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
            existing.subject = normalize_subject(payload.subject)
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
            subject=normalize_subject(payload.subject),
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


async def get_teacher_requests_for_teacher(
    teacher_id: str,
    session: AsyncSession | None = None,
) -> list[TeacherClassJoinRequestResponse]:
    """Get all class join requests made by a specific teacher."""

    async def _do_get(s: AsyncSession):
        stmt = (
            select(TeacherClassJoinRequest)
            .where(TeacherClassJoinRequest.teacherId == teacher_id)
            .options(
                selectinload(TeacherClassJoinRequest.teacher).selectinload(
                    Teacher.user
                ),
                selectinload(TeacherClassJoinRequest.schoolClass),
            )
            .order_by(TeacherClassJoinRequest.requestedAt.desc())
        )
        results = (await s.execute(stmt)).scalars().all()
        return [_to_response(r) for r in results]

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def decide_teacher_class_request(
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
                        subject=req.subject or Subject.MATHS,
                    )
                )

            # Update SchoolClass.teacherId if not set
            cls_stmt = select(SchoolClass).where(SchoolClass.id == req.classId)
            school_cls = (await s.execute(cls_stmt)).scalar_one_or_none()
            if school_cls and not school_cls.teacherId:
                school_cls.teacherId = req.teacherId

            # Also ensure Teacher belongs to this school
            t_stmt = select(Teacher).where(Teacher.id == req.teacherId)
            teacher_obj = (await s.execute(t_stmt)).scalar_one_or_none()
            if teacher_obj and school_cls and not teacher_obj.schoolId:
                teacher_obj.schoolId = school_cls.schoolId

        await s.commit()
        await s.refresh(req)
        return _to_response(req)

    if session:
        return await _do_decide(session)
    async with db.get_session() as s:
        return await _do_decide(s)


# ─── TEACHER SCHOOL JOIN REQUESTS ─────────────────────────────────────────────


async def create_teacher_school_request(
    teacher_id: str,
    school_id: str,
    session: AsyncSession | None = None,
) -> TeacherSchoolJoinRequestResponse:
    """Create a pending request for a teacher to join a school."""

    async def _do_create(s: AsyncSession):
        # 1. Verify school exists
        sch_stmt = select(School).where(School.id == school_id)
        school = (await s.execute(sch_stmt)).scalar_one_or_none()
        if not school:
            raise ValueError("School not found")

        # 2. Check if already part of a school
        t_stmt = select(Teacher).where(Teacher.id == teacher_id)
        teacher = (await s.execute(t_stmt)).scalar_one_or_none()
        if not teacher:
            raise ValueError("Teacher profile not found")
        if teacher.schoolId:
            if teacher.schoolId == school_id:
                raise ValueError("You are already enrolled in this school")
            raise ValueError(
                "You are already enrolled in a school. You cannot join another school until you leave your current school."
            )

        # 3. Check existing request
        existing_stmt = select(TeacherSchoolJoinRequest).where(
            and_(
                TeacherSchoolJoinRequest.teacherId == teacher_id,
                TeacherSchoolJoinRequest.schoolId == school_id,
            )
        )
        existing = (await s.execute(existing_stmt)).scalar_one_or_none()
        if existing:
            if existing.status == JoinRequestStatus.PENDING:
                raise ValueError("A pending request to join this school already exists")
            # If rejected, reopen as PENDING
            existing.status = JoinRequestStatus.PENDING
            existing.requestedAt = datetime.now(UTC)
            existing.decidedAt = None
            existing.decidedBy = None
            await s.commit()
            await s.refresh(existing)
            load_stmt = (
                select(TeacherSchoolJoinRequest)
                .where(TeacherSchoolJoinRequest.id == existing.id)
                .options(
                    selectinload(TeacherSchoolJoinRequest.teacher).selectinload(
                        Teacher.user
                    ),
                    selectinload(TeacherSchoolJoinRequest.school),
                )
            )
            reloaded = (await s.execute(load_stmt)).scalar_one()
            return _to_school_request_response(reloaded)

        # 4. Create new request
        req = TeacherSchoolJoinRequest(
            teacherId=teacher_id,
            schoolId=school_id,
            status=JoinRequestStatus.PENDING,
        )
        s.add(req)
        await s.commit()
        await s.refresh(req)

        load_stmt = (
            select(TeacherSchoolJoinRequest)
            .where(TeacherSchoolJoinRequest.id == req.id)
            .options(
                selectinload(TeacherSchoolJoinRequest.teacher).selectinload(
                    Teacher.user
                ),
                selectinload(TeacherSchoolJoinRequest.school),
            )
        )
        loaded = (await s.execute(load_stmt)).scalar_one()
        return _to_school_request_response(loaded)

    if session:
        return await _do_create(session)
    async with db.get_session() as s:
        return await _do_create(s)


async def get_teacher_school_requests_for_school(
    school_id: str,
    status_filter: str | None = None,
    session: AsyncSession | None = None,
) -> list[TeacherSchoolJoinRequestResponse]:
    """Get all teacher school join requests for a principal's school."""

    async def _do_get(s: AsyncSession):
        stmt = (
            select(TeacherSchoolJoinRequest)
            .where(TeacherSchoolJoinRequest.schoolId == school_id)
            .options(
                selectinload(TeacherSchoolJoinRequest.teacher).selectinload(
                    Teacher.user
                ),
                selectinload(TeacherSchoolJoinRequest.school),
            )
            .order_by(TeacherSchoolJoinRequest.requestedAt.desc())
        )
        if status_filter:
            stmt = stmt.where(TeacherSchoolJoinRequest.status == status_filter)

        results = (await s.execute(stmt)).scalars().all()
        return [_to_school_request_response(r) for r in results]

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def get_teacher_school_requests_for_teacher(
    teacher_id: str,
    session: AsyncSession | None = None,
) -> list[TeacherSchoolJoinRequestResponse]:
    """Get all school join requests submitted by a specific teacher."""

    async def _do_get(s: AsyncSession):
        stmt = (
            select(TeacherSchoolJoinRequest)
            .where(TeacherSchoolJoinRequest.teacherId == teacher_id)
            .options(
                selectinload(TeacherSchoolJoinRequest.teacher).selectinload(
                    Teacher.user
                ),
                selectinload(TeacherSchoolJoinRequest.school),
            )
            .order_by(TeacherSchoolJoinRequest.requestedAt.desc())
        )
        results = (await s.execute(stmt)).scalars().all()
        return [_to_school_request_response(r) for r in results]

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def decide_teacher_school_request(
    request_id: str,
    decision_status: str,
    decided_by_user_name: str,
    session: AsyncSession | None = None,
) -> TeacherSchoolJoinRequestResponse:
    """Approve or Reject a teacher's request to join a school."""

    async def _do_decide(s: AsyncSession):
        stmt = (
            select(TeacherSchoolJoinRequest)
            .where(TeacherSchoolJoinRequest.id == request_id)
            .options(
                selectinload(TeacherSchoolJoinRequest.teacher).selectinload(
                    Teacher.user
                ),
                selectinload(TeacherSchoolJoinRequest.school),
            )
        )
        req = (await s.execute(stmt)).scalar_one_or_none()
        if not req:
            raise ValueError("School join request not found")

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
            # Set teacher.schoolId to school.id
            teacher_stmt = select(Teacher).where(Teacher.id == req.teacherId)
            teacher = (await s.execute(teacher_stmt)).scalar_one_or_none()
            if teacher:
                teacher.schoolId = req.schoolId

            # Add notification
            if req.teacher and hasattr(req.teacher, "userId") and req.teacher.userId:
                s.add(
                    Notification(
                        userId=req.teacher.userId,
                        message=f"Congratulations! Your request to join {req.school.name if req.school else 'the school'} was approved by the Principal.",
                    )
                )
        else:
            if req.teacher and hasattr(req.teacher, "userId") and req.teacher.userId:
                s.add(
                    Notification(
                        userId=req.teacher.userId,
                        message=f"Your request to join {req.school.name if req.school else 'the school'} was declined.",
                    )
                )

        await s.commit()
        await s.refresh(req)
        return _to_school_request_response(req)

    if session:
        return await _do_decide(session)
    async with db.get_session() as s:
        return await _do_decide(s)


# ─── MULTI-CLASS ASSIGNMENT BY PRINCIPAL ──────────────────────────────────────


async def assign_multiple_classes_to_teacher(
    school_id: str,
    teacher_id: str,
    class_ids: list[str],
    subject: str | Subject | None = None,
    session: AsyncSession | None = None,
) -> TeacherAssignClassesResponse:
    """Assign multiple school classes to a teacher in one action."""

    async def _do_assign(s: AsyncSession):
        # Verify teacher belongs to this school
        t_stmt = select(Teacher).where(Teacher.id == teacher_id)
        teacher = (await s.execute(t_stmt)).scalar_one_or_none()
        if not teacher or teacher.schoolId != school_id:
            raise ValueError("Teacher is not enrolled in this school")

        # Verify all classes belong to this school
        cls_stmt = select(SchoolClass).where(
            and_(
                SchoolClass.id.in_(class_ids),
                SchoolClass.schoolId == school_id,
            )
        )
        classes = (await s.execute(cls_stmt)).scalars().all()
        found_class_ids = {c.id for c in classes}
        if len(found_class_ids) != len(class_ids):
            raise ValueError(
                "One or more selected classes do not belong to this school"
            )

        assigned_count = 0
        normalized_subj = normalize_subject(subject) or Subject.MATHS
        for cid in class_ids:
            # Check if TeacherClass exists
            tc_stmt = select(TeacherClass).where(
                and_(
                    TeacherClass.teacherId == teacher_id,
                    TeacherClass.classId == cid,
                )
            )
            existing_tc = (await s.execute(tc_stmt)).scalar_one_or_none()
            if not existing_tc:
                s.add(
                    TeacherClass(
                        teacherId=teacher_id,
                        classId=cid,
                        subject=normalized_subj,
                    )
                )
                assigned_count += 1

        await s.commit()
        return TeacherAssignClassesResponse(
            teacherId=teacher_id,
            classIds=class_ids,
            assignedCount=assigned_count,
            message=f"Successfully assigned {assigned_count} class(es) to teacher.",
        )

    if session:
        return await _do_assign(session)
    async with db.get_session() as s:
        return await _do_assign(s)
