import secrets
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.core.database as db
from app.core.models import SchoolClass
from app.school.crud import get_school_by_user_id
from app.school_class.schemas import (
    SchoolClassCreateRequest,
    SchoolClassResponse,
    SchoolClassUpdateRequest,
)


def generate_join_code() -> str:
    """Generate an easily shareable, case-insensitive class join code."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


async def create_school_class(
    class_data: SchoolClassCreateRequest,
    user_id: str,
    session: AsyncSession | None = None,
) -> SchoolClassResponse | None:
    """Create a class for the authenticated user's school."""
    school = await get_school_by_user_id(user_id, session=session)
    if not school:
        return None

    data_dict = class_data.model_dump()
    data_dict["schoolId"] = school.id

    async def _do_create(s: AsyncSession):
        # A database unique constraint is the final guard; this pre-check makes a
        # (very unlikely) random collision recoverable without exposing an error.
        for _ in range(10):
            join_code = generate_join_code()
            exists = await s.scalar(
                select(SchoolClass.id).where(SchoolClass.joinCode == join_code)
            )
            if not exists:
                data_dict["joinCode"] = join_code
                break
        else:
            raise RuntimeError("Unable to generate a unique class join code")

        school_class = SchoolClass(**data_dict)
        s.add(school_class)
        await s.commit()
        await s.refresh(school_class)
        return SchoolClassResponse.model_validate(school_class)

    if session:
        return await _do_create(session)
    async with db.get_session() as s:
        return await _do_create(s)


async def get_school_classes_by_school_id(
    school_id: str, session: AsyncSession | None = None
) -> list[SchoolClassResponse]:
    """Get all classes for a school."""

    async def _do_get(s: AsyncSession):
        stmt = select(SchoolClass).where(SchoolClass.schoolId == school_id)
        classes = (await s.execute(stmt)).scalars().all()
        return [SchoolClassResponse.model_validate(c) for c in classes]

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def get_school_class_by_id(
    class_id: str, session: AsyncSession | None = None
) -> SchoolClassResponse | None:
    """Get a specific class by its ID."""

    async def _do_get(s: AsyncSession):
        stmt = select(SchoolClass).where(SchoolClass.id == class_id)
        school_class = (await s.execute(stmt)).scalar_one_or_none()
        if not school_class:
            return None
        return SchoolClassResponse.model_validate(school_class)

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def update_school_class(
    class_id: str,
    class_data: SchoolClassUpdateRequest,
    user_id: str,
    session: AsyncSession | None = None,
) -> SchoolClassResponse | None:
    """Update a class that belongs to the authenticated user's school."""
    update_dict = class_data.model_dump(exclude_unset=True)
    if not update_dict:
        return None

    school = await get_school_by_user_id(user_id, session=session)
    if not school:
        return None

    async def _do_update(s: AsyncSession):
        stmt = select(SchoolClass).where(SchoolClass.id == class_id)
        school_class = (await s.execute(stmt)).scalar_one_or_none()
        if not school_class or school_class.schoolId != school.id:
            return None

        for k, v in update_dict.items():
            setattr(school_class, k, v)
        await s.commit()
        await s.refresh(school_class)
        return SchoolClassResponse.model_validate(school_class)

    if session:
        return await _do_update(session)
    async with db.get_session() as s:
        return await _do_update(s)


async def delete_school_class(
    class_id: str, user_id: str, session: AsyncSession | None = None
) -> bool:
    """Delete a class that belongs to the authenticated user's school."""
    school = await get_school_by_user_id(user_id, session=session)
    if not school:
        return False

    async def _do_delete(s: AsyncSession):
        stmt = select(SchoolClass).where(SchoolClass.id == class_id)
        school_class = (await s.execute(stmt)).scalar_one_or_none()
        if not school_class or school_class.schoolId != school.id:
            return False

        await s.delete(school_class)
        await s.commit()
        return True

    if session:
        return await _do_delete(session)
    async with db.get_session() as s:
        return await _do_delete(s)


async def assign_student_to_class(
    class_id: str, student_id: str, session: AsyncSession | None = None
) -> bool:
    """Assign or transfer a student to a class and allocate roll number if needed."""
    from app.core.models import Student

    async def _do_assign(s: AsyncSession):
        cls_stmt = select(SchoolClass).where(SchoolClass.id == class_id)
        school_class = (await s.execute(cls_stmt)).scalar_one_or_none()
        if not school_class:
            return False

        student_stmt = select(Student).where(Student.id == student_id)
        student = (await s.execute(student_stmt)).scalar_one_or_none()
        if not student:
            return False

        student.classId = class_id
        student.schoolId = school_class.schoolId
        await s.commit()
        return True

    if session:
        return await _do_assign(session)
    async with db.get_session() as s:
        return await _do_assign(s)


async def assign_teacher_to_class(
    class_id: str, teacher_id: str, session: AsyncSession | None = None
) -> bool:
    """Assign a teacher to teach a class."""
    from app.core.models import Teacher, TeacherClass

    async def _do_assign(s: AsyncSession):
        cls_stmt = select(SchoolClass).where(SchoolClass.id == class_id)
        school_class = (await s.execute(cls_stmt)).scalar_one_or_none()
        if not school_class:
            return False

        teacher_stmt = select(Teacher).where(Teacher.id == teacher_id)
        teacher = (await s.execute(teacher_stmt)).scalar_one_or_none()
        if not teacher:
            return False

        existing_stmt = select(TeacherClass).where(
            TeacherClass.classId == class_id, TeacherClass.teacherId == teacher_id
        )
        existing = (await s.execute(existing_stmt)).scalar_one_or_none()
        if not existing:
            s.add(TeacherClass(classId=class_id, teacherId=teacher_id))
            await s.commit()
        return True

    if session:
        return await _do_assign(session)
    async with db.get_session() as s:
        return await _do_assign(s)


async def get_class_exam_results(
    class_id: str, session: AsyncSession | None = None
) -> dict:
    """Get aggregated exam results and student performance for a specific class."""
    from sqlalchemy.orm import selectinload

    from app.core.models import Student, StudentExam

    async def _do_get(s: AsyncSession):
        # Fetch all students in the class
        students_stmt = (
            select(Student)
            .where(Student.classId == class_id)
            .options(
                selectinload(Student.user),
                selectinload(Student.studentExams).selectinload(StudentExam.exam),
            )
            .order_by(Student.rollNo)
        )
        students = (await s.execute(students_stmt)).scalars().all()

        student_results = []
        exam_map = {}
        all_percentages = []

        for st in students:
            user = st.user
            attempts_list = []
            for se in st.studentExams or []:
                exam = se.exam
                if not exam:
                    continue
                max_m = exam.maxMarks if exam.maxMarks > 0 else 1
                pct = round((se.marksObtained / max_m) * 100, 2)
                all_percentages.append(pct)

                att_dict = {
                    "attemptId": se.id,
                    "examId": exam.id,
                    "examTitle": exam.name,
                    "examCode": exam.examCode,
                    "subject": (
                        exam.subject.value
                        if exam.subject and hasattr(exam.subject, "value")
                        else (exam.subject or "General")
                    ),
                    "marksObtained": se.marksObtained,
                    "maxMarks": exam.maxMarks,
                    "percentage": pct,
                    "status": (
                        se.status.value
                        if hasattr(se.status, "value")
                        else str(se.status)
                    ),
                    "isResultsReleased": exam.isResultsReleased,
                    "submittedAt": se.submittedAt,
                }
                attempts_list.append(att_dict)

                # Group by exam for class exam breakdown
                if exam.id not in exam_map:
                    exam_map[exam.id] = {
                        "examId": exam.id,
                        "examTitle": exam.name,
                        "examCode": exam.examCode,
                        "subject": (
                            exam.subject.value
                            if exam.subject and hasattr(exam.subject, "value")
                            else (exam.subject or "General")
                        ),
                        "maxMarks": exam.maxMarks,
                        "attemptsCount": 0,
                        "totalMarksSum": 0.0,
                        "highestScore": 0.0,
                        "isResultsReleased": exam.isResultsReleased,
                    }
                e_stat = exam_map[exam.id]
                e_stat["attemptsCount"] += 1
                e_stat["totalMarksSum"] += se.marksObtained
                e_stat["highestScore"] = max(e_stat["highestScore"], se.marksObtained)

            student_results.append(
                {
                    "studentId": st.id,
                    "userId": st.userId,
                    "studentName": user.name if user else "Unknown Student",
                    "email": user.email if user else "",
                    "rollNo": st.rollNo,
                    "totalAttempts": len(attempts_list),
                    "attempts": attempts_list,
                }
            )

        # Calculate exam-level averages
        exams_summary = []
        for _e_id, e_info in exam_map.items():
            count = e_info["attemptsCount"]
            avg_score = round(e_info["totalMarksSum"] / count, 2) if count > 0 else 0.0
            max_m = e_info["maxMarks"] if e_info["maxMarks"] > 0 else 1
            avg_pct = round((avg_score / max_m) * 100, 2)
            exams_summary.append(
                {
                    **e_info,
                    "averageScore": avg_score,
                    "averagePercentage": avg_pct,
                }
            )

        class_avg = (
            round(sum(all_percentages) / len(all_percentages), 2)
            if all_percentages
            else 0.0
        )

        return {
            "classId": class_id,
            "totalStudents": len(students),
            "totalSubmissions": len(all_percentages),
            "classAveragePercentage": class_avg,
            "students": student_results,
            "examsSummary": exams_summary,
        }

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)
