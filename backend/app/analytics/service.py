"""Centralized Analytics and Teacher Results Service.

Handles authorization-scoped metric aggregation, class summaries, student histories,
grading workload summaries, and leaderboards.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.analytics.constants import (
    DEFAULT_PAGE_SIZE,
    DISTINCTION_PERCENTAGE_THRESHOLD,
    MAX_PAGE_SIZE,
    PASSING_PERCENTAGE_THRESHOLD,
)
from app.analytics.schemas import (
    AnalyticsSortBy,
    ClassAnalyticsSummary,
    ClassExamPerformanceItem,
    ClassLeaderboardEntry,
    ClassLeaderboardResponse,
    ClassResultsResponse,
    ExamAnalyticsDetailResponse,
    ExamGradingWorkloadSummary,
    PerformanceBracket,
    SortOrder,
    StudentPerformanceSummary,
    StudentResultHistoryItem,
    StudentResultsResponse,
    TeacherResultsOverviewResponse,
)
from app.attempts.schemas import ExamScoreboardItem
from app.core.models import (
    Exam,
    Role,
    SchoolClass,
    Student,
    StudentExam,
    StudentExamStatus,
    Subject,
    Teacher,
    TeacherClass,
)
from app.exams.crud import get_exam_by_id
from app.exams.permissions import can_manage_exam
from app.grading.crud import get_exam_grading_summary
from app.principals.crud import get_principal_by_teacher_id
from app.school_class.crud import get_school_class_by_id
from app.students.crud import get_student_by_id, get_student_by_user_id
from app.teachers.crud import get_teacher_by_user_id
from app.users.schemas import UserResponse

logger = logging.getLogger("exam_arena.analytics.service")


class AnalyticsService:
    """Service providing authorized analytical summaries and leaderboards."""

    @staticmethod
    async def get_teacher_overview(
        current_user: UserResponse,
        session: AsyncSession,
    ) -> TeacherResultsOverviewResponse:
        """Computes aggregate analytics overview for the authenticated teacher or principal."""
        teacher: Teacher | None = None
        if current_user.role != Role.ADMIN:
            teacher = await get_teacher_by_user_id(current_user.id, session=session)
            if not teacher:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Teacher profile not found for current user",
                )

        # 1. Scope exams by permissions
        exam_stmt = select(Exam.id)
        if current_user.role == Role.TEACHER and teacher:
            exam_stmt = exam_stmt.where(Exam.teacherId == teacher.id)
        elif current_user.role == Role.PRINCIPAL and teacher:
            if not teacher.schoolId:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Principal is not assigned to an active school",
                )
            exam_stmt = exam_stmt.join(Teacher, Exam.teacherId == Teacher.id).where(
                Teacher.schoolId == teacher.schoolId
            )
        # ADMIN: no filter on exams

        exam_ids_result = await session.execute(exam_stmt)
        scoped_exam_ids = [row[0] for row in exam_ids_result.all()]
        total_exams = len(scoped_exam_ids)

        # 2. Scope classes
        class_stmt = select(func.count(func.distinct(SchoolClass.id)))
        if current_user.role == Role.TEACHER and teacher:
            # Classes in teacher's school where teacher is primary teacher or assigned via TeacherClass
            class_stmt = class_stmt.outerjoin(
                TeacherClass, SchoolClass.id == TeacherClass.classId
            ).where(
                SchoolClass.schoolId == teacher.schoolId,
                (SchoolClass.teacherId == teacher.id)
                | (TeacherClass.teacherId == teacher.id),
            )
        elif current_user.role == Role.PRINCIPAL and teacher:
            class_stmt = class_stmt.where(SchoolClass.schoolId == teacher.schoolId)
        # ADMIN: all classes

        classes_count = (await session.execute(class_stmt)).scalar_one() or 0

        if not scoped_exam_ids:
            return TeacherResultsOverviewResponse(
                totalExams=0,
                totalAttempts=0,
                gradedAttempts=0,
                pendingGradingAttempts=0,
                averagePercentage=0.0,
                classes=int(classes_count),
            )

        # 3. Query attempt aggregations scoped strictly to authorized exams
        attempt_stmt = (
            select(
                func.count(StudentExam.id).label("total_attempts"),
                func.count(
                    case(
                        (StudentExam.status == StudentExamStatus.GRADED, StudentExam.id),
                        else_=None,
                    )
                ).label("graded_attempts"),
                func.count(
                    case(
                        (
                            StudentExam.status == StudentExamStatus.SUBMITTED,
                            StudentExam.id,
                        ),
                        else_=None,
                    )
                ).label("pending_grading"),
                func.avg(
                    case(
                        (
                            Exam.maxMarks > 0,
                            (StudentExam.marksObtained / Exam.maxMarks) * 100.0,
                        ),
                        else_=0.0,
                    )
                ).label("avg_percentage"),
            )
            .join(Exam, StudentExam.examId == Exam.id)
            .where(
                StudentExam.examId.in_(scoped_exam_ids),
                StudentExam.status.in_(
                    [StudentExamStatus.SUBMITTED, StudentExamStatus.GRADED]
                ),
            )
        )

        row = (await session.execute(attempt_stmt)).one()
        avg_pct = round(float(row.avg_percentage or 0.0), 2)

        return TeacherResultsOverviewResponse(
            totalExams=total_exams,
            totalAttempts=int(row.total_attempts or 0),
            gradedAttempts=int(row.graded_attempts or 0),
            pendingGradingAttempts=int(row.pending_grading or 0),
            averagePercentage=avg_pct,
            classes=int(classes_count),
        )

    @staticmethod
    async def get_class_analytics(
        class_id: str,
        current_user: UserResponse,
        session: AsyncSession,
        subject: Subject | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> ClassResultsResponse:
        """Calculates comprehensive performance breakdown and exam analytics for a school class."""
        if date_from and date_to and date_from > date_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="dateFrom must be less than or equal to dateTo",
            )

        school_class = await get_school_class_by_id(class_id, session=session)
        if not school_class:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
            )

        # Verify access & cross-school isolation
        await AnalyticsService._verify_class_access(current_user, school_class, session)

        # 1. Fetch students in the class
        student_stmt = (
            select(Student)
            .where(Student.classId == class_id)
            .options(selectinload(Student.user))
            .order_by(Student.rollNo.asc())
        )
        students = (await session.execute(student_stmt)).scalars().all()
        student_ids = [s.id for s in students]
        total_students = len(students)

        if not student_ids:
            return ClassResultsResponse(
                summary=ClassAnalyticsSummary(
                    classId=class_id,
                    className=school_class.name,
                    year=school_class.year,
                    section=school_class.section,
                    totalStudents=0,
                    totalExams=0,
                    totalAttempts=0,
                    gradedAttempts=0,
                    pendingGradingAttempts=0,
                    classAveragePercentage=0.0,
                    highestPercentage=0.0,
                    lowestPercentage=0.0,
                    passRate=0.0,
                    gradingCompletionRate=0.0,
                ),
                exams=[],
            )

        # 2. Build attempts query for enrolled students
        attempts_stmt = (
            select(StudentExam)
            .where(
                StudentExam.studentId.in_(student_ids),
                StudentExam.status.in_(
                    [StudentExamStatus.SUBMITTED, StudentExamStatus.GRADED]
                ),
            )
            .options(
                selectinload(StudentExam.exam).selectinload(Exam.teacher),
                selectinload(StudentExam.student).selectinload(Student.user),
            )
        )

        if date_from:
            attempts_stmt = attempts_stmt.where(StudentExam.submittedAt >= date_from)
        if date_to:
            attempts_stmt = attempts_stmt.where(StudentExam.submittedAt <= date_to)

        attempts = (await session.execute(attempts_stmt)).scalars().all()

        # Teacher authorization filtering: ensure teacher only sees exams they can manage
        teacher: Teacher | None = None
        if current_user.role == Role.TEACHER:
            teacher = await get_teacher_by_user_id(current_user.id, session=session)

        authorized_attempts: list[StudentExam] = []
        for att in attempts:
            exam = att.exam
            if not exam:
                continue
            if subject and exam.subject != subject:
                continue
            # Check exam management permission if teacher
            if current_user.role == Role.TEACHER:
                if not can_manage_exam(current_user, teacher, exam):
                    continue
            authorized_attempts.append(att)

        # Group by exam
        exams_map: dict[str, list[StudentExam]] = {}
        for att in authorized_attempts:
            exams_map.setdefault(att.examId, []).append(att)

        exam_performance_list: list[ClassExamPerformanceItem] = []
        all_percentages: list[float] = []

        for exam_id, exam_attempts in exams_map.items():
            exam = exam_attempts[0].exam
            max_m = exam.maxMarks if exam.maxMarks > 0 else 1
            attempt_percentages = [
                round((att.marksObtained / max_m) * 100.0, 2) for att in exam_attempts
            ]
            all_percentages.extend(attempt_percentages)

            passed_count = sum(
                1 for p in attempt_percentages if p >= PASSING_PERCENTAGE_THRESHOLD
            )
            avg_p = (
                round(sum(attempt_percentages) / len(attempt_percentages), 2)
                if attempt_percentages
                else 0.0
            )
            high_p = max(attempt_percentages) if attempt_percentages else 0.0
            low_p = min(attempt_percentages) if attempt_percentages else 0.0
            pass_rate = (
                round((passed_count / len(attempt_percentages)) * 100.0, 2)
                if attempt_percentages
                else 0.0
            )

            # Get grading workload from Phase A logic
            workload = await get_exam_grading_summary(exam_id, session)

            subject_val = (
                exam.subject.value
                if exam.subject and hasattr(exam.subject, "value")
                else (str(exam.subject) if exam.subject else "General")
            )

            exam_performance_list.append(
                ClassExamPerformanceItem(
                    examId=exam.id,
                    examTitle=exam.name,
                    examCode=exam.examCode,
                    subject=subject_val,
                    maxMarks=exam.maxMarks,
                    studentsAttempted=len(exam_attempts),
                    averagePercentage=avg_p,
                    highestPercentage=high_p,
                    lowestPercentage=low_p,
                    passRate=pass_rate,
                    pendingSubjectiveCount=workload.get("pending", 0),
                    aiSuggestionsReadyCount=workload.get("aiSuggestionsReady", 0),
                    teacherGradedSubjectiveCount=workload.get("teacherGraded", 0),
                    isResultsReleased=exam.isResultsReleased,
                )
            )

        total_attempts = len(authorized_attempts)
        graded_count = sum(
            1 for att in authorized_attempts if att.status == StudentExamStatus.GRADED
        )
        pending_count = total_attempts - graded_count

        class_avg = (
            round(sum(all_percentages) / len(all_percentages), 2)
            if all_percentages
            else 0.0
        )
        highest_pct = max(all_percentages) if all_percentages else 0.0
        lowest_pct = min(all_percentages) if all_percentages else 0.0
        overall_passed = sum(
            1 for p in all_percentages if p >= PASSING_PERCENTAGE_THRESHOLD
        )
        overall_pass_rate = (
            round((overall_passed / len(all_percentages)) * 100.0, 2)
            if all_percentages
            else 0.0
        )
        completion_rate = (
            round((graded_count / total_attempts) * 100.0, 2)
            if total_attempts > 0
            else 0.0
        )

        # Sort exams by title for deterministic response
        exam_performance_list.sort(key=lambda x: x.examTitle.lower())

        summary = ClassAnalyticsSummary(
            classId=class_id,
            className=school_class.name,
            year=school_class.year,
            section=school_class.section,
            totalStudents=total_students,
            totalExams=len(exams_map),
            totalAttempts=total_attempts,
            gradedAttempts=graded_count,
            pendingGradingAttempts=pending_count,
            classAveragePercentage=class_avg,
            highestPercentage=highest_pct,
            lowestPercentage=lowest_pct,
            passRate=overall_pass_rate,
            gradingCompletionRate=completion_rate,
        )

        return ClassResultsResponse(summary=summary, exams=exam_performance_list)

    @staticmethod
    async def get_class_leaderboard(
        class_id: str,
        current_user: UserResponse,
        session: AsyncSession,
        search: str | None = None,
        min_percentage: float | None = None,
        max_percentage: float | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> ClassLeaderboardResponse:
        """Computes class-wide leaderboard aggregating normalized percentages across finalized exams."""
        limit = min(max(1, limit), MAX_PAGE_SIZE)
        offset = max(0, offset)

        school_class = await get_school_class_by_id(class_id, session=session)
        if not school_class:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
            )

        await AnalyticsService._verify_class_access(current_user, school_class, session)

        student_stmt = (
            select(Student)
            .where(Student.classId == class_id)
            .options(
                selectinload(Student.user),
                selectinload(Student.studentExams).selectinload(StudentExam.exam),
            )
        )
        students = (await session.execute(student_stmt)).scalars().all()

        teacher: Teacher | None = None
        if current_user.role == Role.TEACHER:
            teacher = await get_teacher_by_user_id(current_user.id, session=session)

        raw_entries: list[dict[str, Any]] = []

        for st in students:
            user = st.user
            student_name = user.name if user else "Unknown Student"
            roll_no = st.rollNo or ""

            # Search filter
            if search:
                s_lower = search.strip().lower()
                if s_lower not in student_name.lower() and s_lower not in roll_no.lower():
                    continue

            # Compute normalized percentage across finalized exams
            finalized_percentages: list[float] = []
            exams_attempted_count = 0
            passed_count = 0

            for se in st.studentExams or []:
                exam = se.exam
                if not exam:
                    continue
                # If teacher, verify exam can be managed by this teacher
                if current_user.role == Role.TEACHER:
                    if not can_manage_exam(current_user, teacher, exam):
                        continue

                exams_attempted_count += 1

                # Only finalized / graded attempts are counted towards official performance ranking
                if se.status == StudentExamStatus.GRADED:
                    max_m = exam.maxMarks if exam.maxMarks > 0 else 1
                    pct = round((se.marksObtained / max_m) * 100.0, 2)
                    finalized_percentages.append(pct)
                    if pct >= PASSING_PERCENTAGE_THRESHOLD:
                        passed_count += 1

            avg_percentage = (
                round(sum(finalized_percentages) / len(finalized_percentages), 2)
                if finalized_percentages
                else 0.0
            )

            # Filtering on min / max percentage
            if min_percentage is not None and avg_percentage < min_percentage:
                continue
            if max_percentage is not None and avg_percentage > max_percentage:
                continue

            raw_entries.append(
                {
                    "studentId": st.id,
                    "studentName": student_name,
                    "rollNo": roll_no,
                    "examsAttempted": exams_attempted_count,
                    "finalizedExamsCount": len(finalized_percentages),
                    "averagePercentage": avg_percentage,
                    "passedExamsCount": passed_count,
                }
            )

        # Deterministic sorting: averagePercentage desc, rollNo asc, studentName asc
        raw_entries.sort(
            key=lambda item: (
                -item["averagePercentage"],
                item["rollNo"],
                item["studentName"].lower(),
            )
        )

        total_students = len(raw_entries)
        paginated = raw_entries[offset : offset + limit]

        leaderboard: list[ClassLeaderboardEntry] = []
        for idx, entry in enumerate(paginated):
            rank = offset + idx + 1
            leaderboard.append(
                ClassLeaderboardEntry(
                    rank=rank,
                    studentId=entry["studentId"],
                    studentName=entry["studentName"],
                    rollNo=entry["rollNo"],
                    examsAttempted=entry["examsAttempted"],
                    finalizedExamsCount=entry["finalizedExamsCount"],
                    averagePercentage=entry["averagePercentage"],
                    passedExamsCount=entry["passedExamsCount"],
                )
            )

        return ClassLeaderboardResponse(
            classId=class_id,
            className=school_class.name,
            totalStudents=total_students,
            leaderboard=leaderboard,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    async def get_student_results_for_teacher(
        student_id: str,
        current_user: UserResponse,
        session: AsyncSession,
        subject: Subject | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> StudentResultsResponse:
        """Retrieves authorized student performance summary and paginated exam result history."""
        limit = min(max(1, limit), MAX_PAGE_SIZE)
        offset = max(0, offset)

        if date_from and date_to and date_from > date_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="dateFrom must be less than or equal to dateTo",
            )

        student = await get_student_by_id(student_id, session=session)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
            )

        # Check school/role authorization
        teacher = await AnalyticsService._verify_student_access(
            current_user, student, session
        )

        # Retrieve student attempts
        stmt = (
            select(StudentExam)
            .where(
                StudentExam.studentId == student_id,
                StudentExam.status.in_(
                    [StudentExamStatus.SUBMITTED, StudentExamStatus.GRADED]
                ),
            )
            .options(
                selectinload(StudentExam.exam).selectinload(Exam.teacher),
                selectinload(StudentExam.student).selectinload(Student.schoolClass),
            )
            .order_by(StudentExam.submittedAt.desc(), StudentExam.id.asc())
        )

        if date_from:
            stmt = stmt.where(StudentExam.submittedAt >= date_from)
        if date_to:
            stmt = stmt.where(StudentExam.submittedAt <= date_to)

        attempts = (await session.execute(stmt)).scalars().all()

        # Scope exams to what caller may access
        filtered_attempts: list[StudentExam] = []
        for att in attempts:
            exam = att.exam
            if not exam:
                continue
            if subject and exam.subject != subject:
                continue

            if current_user.role == Role.TEACHER:
                if not can_manage_exam(current_user, teacher, exam):
                    continue

            filtered_attempts.append(att)

        finalized_percentages: list[float] = []
        pending_subjective_count = 0
        history_items: list[StudentResultHistoryItem] = []

        for att in filtered_attempts:
            exam = att.exam
            max_m = exam.maxMarks if exam and exam.maxMarks > 0 else 1
            pct = round((att.marksObtained / max_m) * 100.0, 2)
            is_final = att.status == StudentExamStatus.GRADED

            if is_final:
                finalized_percentages.append(pct)
            else:
                pending_subjective_count += 1

            sub_val = (
                exam.subject.value
                if exam.subject and hasattr(exam.subject, "value")
                else (str(exam.subject) if exam.subject else "General")
            )

            history_items.append(
                StudentResultHistoryItem(
                    attemptId=att.id,
                    examId=exam.id,
                    examTitle=exam.name,
                    examCode=exam.examCode,
                    subject=sub_val,
                    date=att.submittedAt or att.startedAt,
                    marksObtained=att.marksObtained,
                    maxMarks=exam.maxMarks,
                    percentage=pct,
                    status=(
                        att.status.value
                        if hasattr(att.status, "value")
                        else str(att.status)
                    ),
                    isFinalized=is_final,
                    classId=student.classId,
                    className=student.className,
                )
            )

        # Performance summary on finalized attempts only
        total_exams = len(filtered_attempts)
        passed_count = sum(
            1 for p in finalized_percentages if p >= PASSING_PERCENTAGE_THRESHOLD
        )
        failed_count = sum(
            1 for p in finalized_percentages if p < PASSING_PERCENTAGE_THRESHOLD
        )
        avg_pct = (
            round(sum(finalized_percentages) / len(finalized_percentages), 2)
            if finalized_percentages
            else 0.0
        )
        high_pct = max(finalized_percentages) if finalized_percentages else 0.0
        low_pct = min(finalized_percentages) if finalized_percentages else 0.0

        user_name = student.user.name if student.user else "Student"

        summary = StudentPerformanceSummary(
            studentId=student.id,
            studentName=user_name,
            rollNo=student.rollNo,
            totalExams=total_exams,
            averagePercentage=avg_pct,
            highestPercentage=high_pct,
            lowestPercentage=low_pct,
            passed=passed_count,
            failed=failed_count,
            pendingSubjectiveGradingExams=pending_subjective_count,
        )

        total_count = len(history_items)
        paginated_history = history_items[offset : offset + limit]

        return StudentResultsResponse(
            summary=summary,
            history=paginated_history,
            limit=limit,
            offset=offset,
            totalCount=total_count,
        )

    @staticmethod
    async def get_exam_analytics(
        exam_id: str,
        current_user: UserResponse,
        session: AsyncSession,
        search: str | None = None,
        bracket: PerformanceBracket = PerformanceBracket.ALL,
        min_percentage: float | None = None,
        max_percentage: float | None = None,
        sort_by: AnalyticsSortBy = AnalyticsSortBy.RANK,
        sort_order: SortOrder = SortOrder.ASC,
        limit: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> ExamAnalyticsDetailResponse:
        """Calculates detailed exam-level analytics, workload counts, and filtered/sorted leaderboard."""
        limit = min(max(1, limit), MAX_PAGE_SIZE)
        offset = max(0, offset)

        exam = await get_exam_by_id(exam_id, session=session)
        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found"
            )

        # Authorize caller to manage this exam
        teacher: Teacher | None = None
        if current_user.role != Role.ADMIN:
            teacher = await get_teacher_by_user_id(current_user.id, session=session)
            if not can_manage_exam(current_user, teacher, exam):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access analytics for this exam",
                )

        # 1. Workload counts using Phase A logic
        workload_data = await get_exam_grading_summary(exam_id, session)
        workload = ExamGradingWorkloadSummary(
            totalSubjectiveAnswers=workload_data.get("totalSubjectiveAnswers", 0),
            pendingSubjectiveCount=workload_data.get("pending", 0),
            aiSuggestionsReadyCount=workload_data.get("aiSuggestionsReady", 0),
            teacherGradedSubjectiveCount=workload_data.get("teacherGraded", 0),
        )

        # 2. Fetch all student attempts for this exam with deterministic tie-break ordering
        stmt = (
            select(StudentExam)
            .where(StudentExam.examId == exam_id)
            .options(selectinload(StudentExam.student).selectinload(Student.user))
            .order_by(StudentExam.marksObtained.desc(), StudentExam.id.asc())
        )
        results = (await session.execute(stmt)).scalars().all()

        max_marks = exam.maxMarks if exam.maxMarks > 0 else 1
        all_items: list[ExamScoreboardItem] = []
        all_percentages: list[float] = []
        graded_count = 0
        pending_count = 0

        for i, se in enumerate(results):
            student = se.student
            user = student.user if student else None
            student_name = user.name if user else "Unknown"
            roll_no = student.rollNo if student else ""
            pct = round((se.marksObtained / max_marks) * 100.0, 2)
            all_percentages.append(pct)

            if se.status == StudentExamStatus.GRADED:
                graded_count += 1
            elif se.status == StudentExamStatus.SUBMITTED:
                pending_count += 1

            item = ExamScoreboardItem(
                rank=i + 1,
                attemptId=se.id,
                studentId=student.id if student else "",
                studentName=student_name,
                rollNo=roll_no,
                marksObtained=se.marksObtained,
                maxMarks=exam.maxMarks,
                percentage=pct,
                status=(
                    se.status.value
                    if hasattr(se.status, "value")
                    else str(se.status)
                ),
                startedAt=se.startedAt,
                submittedAt=se.submittedAt,
            )
            all_items.append(item)

        # Compute overarching statistics before applying pagination/filters
        total_attempts = len(all_items)
        avg_pct = (
            round(sum(all_percentages) / len(all_percentages), 2)
            if all_percentages
            else 0.0
        )
        high_pct = max(all_percentages) if all_percentages else 0.0
        low_pct = min(all_percentages) if all_percentages else 0.0
        passed_count = sum(
            1 for p in all_percentages if p >= PASSING_PERCENTAGE_THRESHOLD
        )
        pass_rate = (
            round((passed_count / len(all_percentages)) * 100.0, 2)
            if all_percentages
            else 0.0
        )

        # 3. Apply filters to leaderboard
        filtered_items = all_items

        if search and search.strip():
            q = search.strip().lower()
            filtered_items = [
                it
                for it in filtered_items
                if q in it.studentName.lower() or q in it.rollNo.lower()
            ]

        if bracket == PerformanceBracket.PASSED:
            filtered_items = [
                it for it in filtered_items if it.percentage >= PASSING_PERCENTAGE_THRESHOLD
            ]
        elif bracket == PerformanceBracket.FAILED:
            filtered_items = [
                it for it in filtered_items if it.percentage < PASSING_PERCENTAGE_THRESHOLD
            ]
        elif bracket == PerformanceBracket.DISTINCTION:
            filtered_items = [
                it
                for it in filtered_items
                if it.percentage >= DISTINCTION_PERCENTAGE_THRESHOLD
            ]

        if min_percentage is not None:
            filtered_items = [
                it for it in filtered_items if it.percentage >= min_percentage
            ]
        if max_percentage is not None:
            filtered_items = [
                it for it in filtered_items if it.percentage <= max_percentage
            ]

        # 4. Safe sorting
        reverse = sort_order == SortOrder.DESC
        if sort_by == AnalyticsSortBy.SCORE or sort_by == AnalyticsSortBy.PERCENTAGE:
            filtered_items.sort(
                key=lambda x: (x.marksObtained, -x.rank), reverse=reverse
            )
        elif sort_by == AnalyticsSortBy.NAME:
            filtered_items.sort(
                key=lambda x: x.studentName.lower(), reverse=reverse
            )
        elif sort_by == AnalyticsSortBy.ROLL_NO:
            filtered_items.sort(key=lambda x: x.rollNo, reverse=reverse)
        elif sort_by == AnalyticsSortBy.SUBMITTED_AT:
            filtered_items.sort(
                key=lambda x: x.submittedAt or datetime.min, reverse=reverse
            )
        else:
            # Default RANK
            filtered_items.sort(key=lambda x: x.rank, reverse=reverse)

        total_filtered_count = len(filtered_items)
        paginated_items = filtered_items[offset : offset + limit]

        sub_val = (
            exam.subject.value
            if exam.subject and hasattr(exam.subject, "value")
            else (str(exam.subject) if exam.subject else "General")
        )

        return ExamAnalyticsDetailResponse(
            examId=exam.id,
            examTitle=exam.name,
            examCode=exam.examCode,
            subject=sub_val,
            maxMarks=exam.maxMarks,
            totalAttempts=total_attempts,
            gradedAttempts=graded_count,
            pendingGradingAttempts=pending_count,
            averagePercentage=avg_pct,
            highestPercentage=high_pct,
            lowestPercentage=low_pct,
            passRate=pass_rate,
            workload=workload,
            leaderboard=paginated_items,
            totalCount=total_filtered_count,
            limit=limit,
            offset=offset,
        )

    # ─────────────────────────────────────────────────────────────────────────────
    # Authorization & Tenant Isolation Helpers
    # ─────────────────────────────────────────────────────────────────────────────

    @staticmethod
    async def _verify_class_access(
        current_user: UserResponse,
        school_class: Any,
        session: AsyncSession,
    ) -> Teacher | None:
        """Validates that current user is authorized to view analytics for this class."""
        if current_user.role == Role.ADMIN:
            return None

        teacher = await get_teacher_by_user_id(current_user.id, session=session)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Staff profile not found",
            )

        if not teacher.schoolId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Staff is not assigned to an active school",
            )

        # Cross-school tenant isolation: School A staff cannot view School B class
        if teacher.schoolId != school_class.schoolId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Class belongs to a different school.",
            )

        return teacher

    @staticmethod
    async def _verify_student_access(
        current_user: UserResponse,
        student: Student,
        session: AsyncSession,
    ) -> Teacher | None:
        """Validates that current user is authorized to view student history and analytics."""
        if current_user.role == Role.ADMIN:
            return None

        if current_user.role == Role.STUDENT:
            if student.userId != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Students can only view their own results.",
                )
            return None

        teacher = await get_teacher_by_user_id(current_user.id, session=session)
        if not teacher or not teacher.schoolId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Staff is not assigned to an active school.",
            )

        # Cross-school isolation: School A teacher cannot view School B student
        if teacher.schoolId != student.schoolId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Student belongs to a different school.",
            )

        return teacher
