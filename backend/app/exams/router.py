from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status  # type: ignore

import app.exams.crud as crud
from app.api.deps import get_current_user
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
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to create exam. Please retry.",
        ) from exc


@router.get("", response_model=list[ExamResponse])
async def list_my_exams_teacher(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    teacher = await get_teacher_from_user(current_user)
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

    if not exam.teacher or exam.teacher.id != teacher.id:
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

    if not exam.teacher or exam.teacher.id != teacher.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to release results for this exam",
        )

    released = await crud.release_results(exam_id)
    if not released:
        raise HTTPException(status_code=404, detail="Exam not found")
    return released
