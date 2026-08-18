from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status  # type: ignore
from pydantic import ValidationError

import app.exams.crud as crud
from app.api.deps import get_current_user
from app.attempts.schemas import ExamScoreboardItem
from app.audit.actions import AuditAction, AuditResourceType
from app.audit.service import record_audit_event
from app.core.models import Role, StudentExamStatus
from app.exams.permissions import can_manage_exam, redact_exam_solutions
from app.exams.schemas import (
    ExamCreateRequest,
    ExamResponse,
    ExamUpdateRequest,
    StudentExamListItemResponse,
)
from app.teachers.crud import get_teacher_by_user_id
from app.users.schemas import UserResponse

router = APIRouter(prefix="/api/v1/exams", tags=["exams"])


async def get_teacher_from_user(user: UserResponse):
    teacher = await get_teacher_by_user_id(user.id)
    if not teacher:
        raise HTTPException(status_code=403, detail="Only teachers can manage exams")
    return teacher


async def require_exam_manager(current_user: UserResponse, exam: ExamResponse):
    teacher = None
    if current_user.role != Role.ADMIN:
        teacher = await get_teacher_by_user_id(current_user.id)
    if not can_manage_exam(current_user, teacher, exam):
        raise HTTPException(
            status_code=403, detail="Not authorized to manage this exam"
        )
    return teacher


@router.post("", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_new_exam(
    exam_data: ExamCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    if current_user.role not in (Role.TEACHER, Role.PRINCIPAL):
        raise HTTPException(status_code=403, detail="Only teachers can manage exams")
    teacher = await get_teacher_from_user(current_user)
    if not teacher.schoolId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must first join and be approved by a School before creating exams.",
        )
    try:
        exam = await crud.create_exam(exam_data, teacher.id)
        await record_audit_event(
            action=AuditAction.EXAM_CREATED,
            resource_type=AuditResourceType.EXAM,
            resource_id=exam.id,
            metadata={"name": exam.name, "type": exam.type, "duration": exam.duration},
        )
        return exam
    except HTTPException:
        raise
    except (ValueError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create exam: {exc}",
        ) from exc


@router.get("", response_model=list[ExamResponse])
async def list_my_exams_teacher(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    if current_user.role == "ADMIN":
        return await crud.get_all_exams_admin()

    teacher = await get_teacher_from_user(current_user)
    if current_user.role == "PRINCIPAL":
        if teacher.schoolId:
            return await crud.get_exams_by_school(teacher.schoolId)
        return await crud.get_exams_by_teacher(teacher.id)

    return await crud.get_exams_by_teacher(teacher.id)


@router.get("/public", response_model=list[ExamResponse])
async def list_published_exams(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    name: str | None = None,
    type: str | None = None,
    teacher_name: str | None = None,
    school_name: str | None = None,
    subject: str | None = None,
    code: str | None = None,
):
    # 🔥 RBAC: restrict by school
    school_id = None
    if (
        current_user.role == "PRINCIPAL" or current_user.role == "TEACHER"
    ):  # only ADMIN sees all
        teacher = await get_teacher_by_user_id(current_user.id)
        if teacher:
            school_id = teacher.schoolId
    exams = await crud.get_published_exams(
        name=name,
        exam_type=type,
        teacher_name=teacher_name,
        school_name=school_name,
        subject=subject,
        school_id=school_id,
        code=code,
    )
    return [redact_exam_solutions(exam, include_questions=False) for exam in exams]


@router.get("/student", response_model=list[StudentExamListItemResponse])
async def list_student_exams(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    name: str | None = None,
    type: str | None = None,
    subject: str | None = None,
    code: str | None = None,
):
    if current_user.role != "STUDENT":
        raise HTTPException(
            status_code=403, detail="Only students can access this endpoint"
        )

    from app.students.crud import get_student_by_user_id

    student = await get_student_by_user_id(current_user.id)
    if not student:
        raise HTTPException(status_code=400, detail="Student profile not found")

    results = await crud.get_published_exams_for_student(
        student_id=student.id,
        school_id=student.schoolId,
        name=name,
        exam_type=type,
        subject=subject,
        code=code,
    )

    return [
        redact_exam_solutions(
            StudentExamListItemResponse.model_validate(result),
            include_questions=False,
        )
        for result in results
    ]


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    exam = await crud.get_exam_by_id(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    if current_user.role == Role.STUDENT:
        from sqlalchemy import select

        import app.core.database as db
        from app.core.models import StudentExam
        from app.students.crud import get_student_by_user_id

        student = await get_student_by_user_id(current_user.id)
        if not student:
            raise HTTPException(status_code=403, detail="Student profile not found")

        async with db.get_session() as session:
            stmt = select(StudentExam).where(
                StudentExam.studentId == student.id,
                StudentExam.examId == exam_id,
            )
            student_exam = (await session.execute(stmt)).scalar_one_or_none()

        if not student_exam:
            if not exam.isPublished:
                raise HTTPException(status_code=404, detail="Exam not found")
            return redact_exam_solutions(exam, include_questions=False)

        return redact_exam_solutions(
            exam,
            include_questions=student_exam.status == StudentExamStatus.IN_PROGRESS
            or exam.isResultsReleased,
            reveal_solutions=exam.isResultsReleased,
        )

    teacher = await get_teacher_by_user_id(current_user.id)
    if can_manage_exam(current_user, teacher, exam):
        return exam
    if not exam.isPublished:
        raise HTTPException(status_code=404, detail="Exam not found")
    return redact_exam_solutions(exam, include_questions=False)


@router.patch("/{exam_id}", response_model=ExamResponse)
async def patch_exam(
    exam_id: str,
    update_data: ExamUpdateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    exam = await crud.get_exam_by_id(exam_id)

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    await require_exam_manager(current_user, exam)

    updated = await crud.update_exam(exam_id, update_data)
    await record_audit_event(
        action=AuditAction.EXAM_UPDATED,
        resource_type=AuditResourceType.EXAM,
        resource_id=exam_id,
        metadata=update_data.model_dump(exclude_unset=True),
    )
    return updated


@router.post("/{exam_id}/release-results", response_model=ExamResponse)
async def release_exam_results(
    exam_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    exam = await crud.get_exam_by_id(exam_id)

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    await require_exam_manager(current_user, exam)

    released = await crud.release_results(exam_id)
    if not released:
        raise HTTPException(status_code=404, detail="Exam not found")

    await record_audit_event(
        action=AuditAction.EXAM_RESULTS_RELEASED,
        resource_type=AuditResourceType.EXAM,
        resource_id=exam_id,
    )
    return released


@router.get("/{exam_id}/results", response_model=list[ExamScoreboardItem])
async def get_exam_results_endpoint(
    exam_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """Get all student results and leaderboard for an exam (Teacher owner, Principal, or Admin)"""
    exam = await crud.get_exam_by_id(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    await require_exam_manager(current_user, exam)
    return await crud.get_exam_results(exam_id)


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam_endpoint(
    exam_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    exam = await crud.get_exam_by_id(exam_id)

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    await require_exam_manager(current_user, exam)

    deleted = await crud.delete_exam(exam_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Exam not found")

    await record_audit_event(
        action=AuditAction.EXAM_DELETED,
        resource_type=AuditResourceType.EXAM,
        resource_id=exam_id,
    )
