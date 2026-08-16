from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status  # type: ignore
from pydantic import ValidationError

import app.exams.crud as crud
from app.api.deps import get_current_user
from app.attempts.schemas import ExamScoreboardItem
from app.core.models import Role
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


@router.post("", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_new_exam(
    exam_data: ExamCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    teacher = await get_teacher_from_user(current_user)
    try:
        return await crud.create_exam(exam_data, teacher.id)
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
    return await crud.get_published_exams(
        name=name,
        exam_type=type,
        teacher_name=teacher_name,
        school_name=school_name,
        subject=subject,
        school_id=school_id,
        code=code,
    )  # type: ignore


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

    return [StudentExamListItemResponse.model_validate(r) for r in results]


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    exam = await crud.get_exam_by_id(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Block student access to the full exam detail API if they aren't explicitly enrolled
    # or even if they are enrolled, they shouldn't view full questions details this way unless allowed
    if current_user.role == "STUDENT":
        from sqlalchemy import select

        import app.core.database as db
        from app.core.models import StudentExam
        from app.students.crud import get_student_by_user_id

        student = await get_student_by_user_id(current_user.id)
        if student:
            async with db.get_session() as session:
                stmt = select(StudentExam).where(
                    StudentExam.studentId == student.id,
                    StudentExam.examId == exam_id,
                )
                student_exam = (await session.execute(stmt)).scalar_one_or_none()
            if not student_exam:
                exam.questionCount = len(exam.questions) if exam.questions else 0
                exam.questions = []
            else:
                exam.questionCount = len(exam.questions) if exam.questions else 0
        else:
            exam.questionCount = len(exam.questions) if exam.questions else 0
            exam.questions = []

    return exam


@router.patch("/{exam_id}", response_model=ExamResponse)
async def patch_exam(
    exam_id: str,
    update_data: ExamUpdateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    teacher = await get_teacher_from_user(current_user)
    exam = await crud.get_exam_by_id(exam_id)

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    is_owner = exam.teacher and exam.teacher.id == teacher.id
    if not is_owner:
        if current_user.role == "PRINCIPAL":
            exam_teacher = exam.teacher
            if (
                not exam_teacher
                or not exam_teacher.school
                or exam_teacher.school.id != teacher.schoolId
            ):
                if teacher.schoolId is None or (
                    hasattr(exam_teacher, "schoolId")
                    and exam_teacher.schoolId != teacher.schoolId
                ):
                    raise HTTPException(
                        status_code=403,
                        detail="Not authorized to edit exams from other schools",
                    )
        elif current_user.role != "ADMIN":
            raise HTTPException(status_code=403, detail="Not authorized")

    return await crud.update_exam(exam_id, update_data)


@router.post("/{exam_id}/release-results", response_model=ExamResponse)
async def release_exam_results(
    exam_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    teacher = await get_teacher_from_user(current_user)
    exam = await crud.get_exam_by_id(exam_id)

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    is_owner = exam.teacher and exam.teacher.id == teacher.id
    if not is_owner:
        if current_user.role == "PRINCIPAL":
            exam_teacher = exam.teacher
            if (
                not exam_teacher
                or not exam_teacher.school
                or exam_teacher.school.id != teacher.schoolId
            ):
                if teacher.schoolId is None or (
                    hasattr(exam_teacher, "schoolId")
                    and exam_teacher.schoolId != teacher.schoolId
                ):
                    raise HTTPException(
                        status_code=403,
                        detail="Not authorized to release results for exams from other schools",
                    )
        elif current_user.role != "ADMIN":
            raise HTTPException(
                status_code=403,
                detail="Not authorized to release results for this exam",
            )

    released = await crud.release_results(exam_id)
    if not released:
        raise HTTPException(status_code=404, detail="Exam not found")
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

    if current_user.role == Role.ADMIN:
        return await crud.get_exam_results(exam_id)

    if current_user.role == Role.PRINCIPAL:
        from app.school.crud import get_school_by_user_id

        school = await get_school_by_user_id(current_user.id)
        teacher = await get_teacher_by_user_id(current_user.id)
        school_id = school.id if school else (teacher.schoolId if teacher else None)

        exam_teacher = exam.teacher
        exam_school_id = (
            exam_teacher.school.id
            if (exam_teacher and exam_teacher.school)
            else getattr(exam_teacher, "schoolId", None)
        )

        if school_id and exam_school_id and school_id != exam_school_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view results for exams from other schools",
            )
        return await crud.get_exam_results(exam_id)

    teacher = await get_teacher_by_user_id(current_user.id)
    is_owner = bool(teacher and exam.teacher and exam.teacher.id == teacher.id)

    if not is_owner:
        raise HTTPException(
            status_code=403,
            detail="Only the exam owner teacher, principal, or admin can view results.",
        )

    return await crud.get_exam_results(exam_id)


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam_endpoint(
    exam_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    teacher = await get_teacher_from_user(current_user)
    exam = await crud.get_exam_by_id(exam_id)

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    is_owner = exam.teacher and exam.teacher.id == teacher.id
    if not is_owner:
        if current_user.role == "PRINCIPAL":
            exam_teacher = exam.teacher
            if (
                not exam_teacher
                or not exam_teacher.school
                or exam_teacher.school.id != teacher.schoolId
            ):
                if teacher.schoolId is None or (
                    hasattr(exam_teacher, "schoolId")
                    and exam_teacher.schoolId != teacher.schoolId
                ):
                    raise HTTPException(
                        status_code=403,
                        detail="Not authorized to delete exams from other schools",
                    )
        elif current_user.role != "ADMIN":
            raise HTTPException(status_code=403, detail="Not authorized")

    deleted = await crud.delete_exam(exam_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Exam not found")
