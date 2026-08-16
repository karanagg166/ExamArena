from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import app.core.database as db
from app.attempts.schemas import (
    StudentExamCreate,
    StudentExamResponse,
    StudentExamSubmit,
)
from app.core.models import (
    Correctness,
    Exam,
    GradingStatus,
    Question,
    QuestionType,
    SelectedOption,
    StudentExam,
    StudentExamAnswer,
    StudentExamStatus,
)

AttemptStatus = StudentExamStatus
from app.students.crud import get_student_by_user_id

STUDENT_EXAM_OPTIONS = [
    selectinload(StudentExam.exam),
    selectinload(StudentExam.answers).selectinload(StudentExamAnswer.selectedOptions),
]


async def start_exam_attempt(
    attempt_data: StudentExamCreate, user_id: str, session: AsyncSession | None = None
) -> StudentExamResponse:
    student = await get_student_by_user_id(user_id, session=session)
    if not student:
        raise ValueError("Only students can start an exam")
    if not student.schoolId or not student.classId:
        raise ValueError(
            "You must first join a school and class using your class join code and get approved before taking exams."
        )

    async def _do_start(s: AsyncSession):
        exam_stmt = (
            select(Exam)
            .where(Exam.id == attempt_data.examId)
            .options(
                selectinload(Exam.questions),
                selectinload(Exam.teacher),
            )
        )
        exam = (await s.execute(exam_stmt)).scalar_one_or_none()
        if not exam:
            raise ValueError("Exam not found")
        if not exam.isPublished:
            raise ValueError("This exam is not currently published")

        # 1. Check School authorization: Student must belong to same school as exam teacher
        if not exam.teacher or student.schoolId != exam.teacher.schoolId:
            raise ValueError("You are not enrolled in the school offering this exam")

        # 2. Check scheduled date & time: After scheduled time, students can take exams anytime
        now = datetime.now(UTC)
        if exam.scheduledAt:
            scheduled_time = (
                exam.scheduledAt
                if exam.scheduledAt.tzinfo
                else exam.scheduledAt.replace(tzinfo=UTC)
            )
            # Allow start if current time is equal to or past scheduled time (with small grace)
            if now < scheduled_time:
                raise ValueError(
                    f"This exam is scheduled for {scheduled_time.strftime('%Y-%m-%d %H:%M UTC')}. "
                    "You can take it any time after the scheduled start time."
                )

        # 3. Check access code if exam is not public
        if not exam.isPublic:
            password_input = (attempt_data.examCode or "").strip()
            if not exam.accessPassword or password_input != exam.accessPassword.strip():
                raise ValueError(
                    "This exam requires a valid access password. Please enter the correct password to proceed."
                )

        # Check for existing attempt
        existing_stmt = (
            select(StudentExam)
            .where(StudentExam.studentId == student.id, StudentExam.examId == exam.id)
            .options(*STUDENT_EXAM_OPTIONS)
        )
        existing = (await s.execute(existing_stmt)).scalar_one_or_none()
        if existing:
            resp = StudentExamResponse.model_validate(existing)
            resp.isResultsReleased = (
                existing.exam.isResultsReleased if existing.exam else False
            )
            return resp

        # Create attempt & answers
        answers_payload = [
            StudentExamAnswer(
                questionId=q.id,
                questionType=q.questionType,
                gradingStatus=GradingStatus.PENDING,
            )
            for q in (exam.questions or [])
        ]

        new_attempt = StudentExam(
            studentId=student.id,
            examId=exam.id,
            status=AttemptStatus.IN_PROGRESS,
            startedAt=datetime.now(UTC),
            answers=answers_payload,
        )
        s.add(new_attempt)
        await s.commit()

        res_stmt = (
            select(StudentExam)
            .where(StudentExam.id == new_attempt.id)
            .options(*STUDENT_EXAM_OPTIONS)
        )
        attempt_obj = (await s.execute(res_stmt)).scalar_one()
        resp = StudentExamResponse.model_validate(attempt_obj)
        resp.isResultsReleased = (
            attempt_obj.exam.isResultsReleased if attempt_obj.exam else False
        )
        return resp

    if session:
        return await _do_start(session)
    async with db.get_session() as s:
        return await _do_start(s)


async def get_attempt_by_id(
    attempt_id: str, session: AsyncSession | None = None
) -> StudentExamResponse | None:

    async def _do_get(s: AsyncSession):
        stmt = (
            select(StudentExam)
            .where(StudentExam.id == attempt_id)
            .options(*STUDENT_EXAM_OPTIONS)
        )
        attempt_model = (await s.execute(stmt)).scalar_one_or_none()
        if not attempt_model:
            return None
        resp = StudentExamResponse.model_validate(attempt_model)
        resp.isResultsReleased = (
            attempt_model.exam.isResultsReleased if attempt_model.exam else False
        )
        return resp

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)


async def submit_exam_attempt(
    submit_data: StudentExamSubmit, user_id: str, session: AsyncSession | None = None
) -> StudentExamResponse:
    student = await get_student_by_user_id(user_id, session=session)
    if not student:
        raise ValueError("Only students can submit an exam")
    attempt = await get_attempt_by_id(submit_data.id, session=session)
    if not attempt:
        raise ValueError("Attempt not found")

    if attempt.studentId != student.id:
        raise ValueError("Not authorized to submit this attempt")

    async def _do_submit(s: AsyncSession):
        # Fetch attempt with exam and all questions + options + sections
        attempt_stmt = (
            select(StudentExam)
            .where(StudentExam.id == submit_data.id)
            .options(
                selectinload(StudentExam.exam)
                .selectinload(Exam.questions)
                .selectinload(Question.options),
                selectinload(StudentExam.exam)
                .selectinload(Exam.questions)
                .selectinload(Question.examSection),
                selectinload(StudentExam.exam).selectinload(Exam.sections),
                selectinload(StudentExam.answers).selectinload(
                    StudentExamAnswer.selectedOptions
                ),
            )
        )
        db_attempt = (await s.execute(attempt_stmt)).scalar_one_or_none()
        if not db_attempt:
            raise ValueError("Attempt not found")

        if db_attempt.status in (AttemptStatus.SUBMITTED, AttemptStatus.GRADED):
            raise ValueError("This exam has already been submitted and attempted.")

        db_answers_by_id = {answer.id: answer for answer in db_attempt.answers or []}
        submitted_answer_ids = {answer.id for answer in submit_data.answers}
        unknown_answer_ids = submitted_answer_ids - db_answers_by_id.keys()
        if unknown_answer_ids:
            raise ValueError(
                "Submission contains answers that do not belong to this attempt"
            )

        for submitted_answer in submit_data.answers:
            db_answer = db_answers_by_id[submitted_answer.id]
            question = next(
                (
                    item
                    for item in (db_attempt.exam.questions or [])
                    if item.id == db_answer.questionId
                ),
                None,
            )
            valid_option_ids = (
                {option.id for option in (question.options or [])}
                if question
                else set()
            )
            selected_option_ids = {
                option.optionId for option in (submitted_answer.selectedOptions or [])
            }
            if not selected_option_ids.issubset(valid_option_ids):
                raise ValueError(
                    "Submission contains options that do not belong to the answer's question"
                )

        exam = db_attempt.exam
        now = datetime.now(UTC)

        # Enforce server-side timing: startedAt + duration + 1 min grace period
        duration_val = getattr(exam, "duration", None)
        if (
            exam
            and isinstance(duration_val, (int, float))
            and duration_val > 0
            and getattr(db_attempt, "startedAt", None)
            and isinstance(db_attempt.startedAt, datetime)
        ):
            started_at = (
                db_attempt.startedAt
                if db_attempt.startedAt.tzinfo
                else db_attempt.startedAt.replace(tzinfo=UTC)
            )
            # 1 minute network latency grace period
            allowed_deadline = (
                started_at
                + timedelta(minutes=float(duration_val))
                + timedelta(minutes=1)
            )
            if now > allowed_deadline:
                raise ValueError(
                    "Exam submission time exceeded. The deadline for this exam has passed."
                )

        questions_by_id = {q.id: q for q in (exam.questions or [])}
        sections_by_id = {sec.id: sec for sec in (exam.sections or [])}
        sections_by_name = {sec.name: sec for sec in (exam.sections or [])}

        total_marks_obtained = 0.0
        has_pending_subjective = False

        # Build answers map from submission
        submitted_answers_map = {ans.id: ans for ans in submit_data.answers}

        # Batch delete existing selectedOptions for all submitted answers in a single query
        ans_ids_with_options = [
            ans.id for ans in submit_data.answers if ans.selectedOptions is not None
        ]
        if ans_ids_with_options:
            await s.execute(
                delete(SelectedOption).where(
                    SelectedOption.studentExamAnswerId.in_(ans_ids_with_options)
                )
            )

        for db_ans in db_attempt.answers or []:
            ans = submitted_answers_map.get(db_ans.id)
            if ans:
                if ans.textAnswer is not None:
                    db_ans.textAnswer = ans.textAnswer
                if ans.selectedOptions is not None:
                    db_ans.selectedOptions = [
                        SelectedOption(optionId=o.optionId) for o in ans.selectedOptions
                    ]

            # Auto-grade based on question type
            q = questions_by_id.get(db_ans.questionId)
            if not q:
                continue

            q_marks = float(q.marks)

            # Determine section-level negative marking policy
            section_obj = (
                q.examSection
                or (sections_by_id.get(q.sectionId) if q.sectionId else None)
                or (sections_by_name.get(q.section) if q.section else None)
            )
            if section_obj:
                sec_has_neg = section_obj.negativeMarking
                sec_neg_marks = float(section_obj.negativeMarks)
            else:
                sec_has_neg = exam.negativeMarking
                sec_neg_marks = float(exam.negativeMarks)

            q_neg = getattr(q, "negativeMarks", None)
            if q_neg is not None:
                neg_marks = float(q_neg)
                has_neg = True
            elif sec_has_neg:
                neg_marks = sec_neg_marks
                has_neg = sec_neg_marks > 0
            else:
                neg_marks = 0.0
                has_neg = False

            penalty = abs(neg_marks) if (has_neg and neg_marks > 0) else 0.0

            selected_opt_ids = {so.optionId for so in (db_ans.selectedOptions or [])}
            correct_opt_ids = {opt.id for opt in (q.options or []) if opt.isCorrect}

            if db_ans.questionType in (
                QuestionType.MULTIPLE_CHOICE,
                QuestionType.TRUE_FALSE,
            ):
                if not selected_opt_ids:
                    db_ans.marksAwarded = 0.0
                    db_ans.isCorrect = Correctness.INCORRECT
                    db_ans.gradingStatus = GradingStatus.AUTO_GRADED
                elif selected_opt_ids == correct_opt_ids:
                    db_ans.marksAwarded = q_marks
                    db_ans.isCorrect = Correctness.FULLY_CORRECT
                    db_ans.gradingStatus = GradingStatus.AUTO_GRADED
                    total_marks_obtained += q_marks
                else:
                    db_ans.marksAwarded = -penalty
                    db_ans.isCorrect = Correctness.INCORRECT
                    db_ans.gradingStatus = GradingStatus.AUTO_GRADED
                    total_marks_obtained -= penalty

            elif db_ans.questionType == QuestionType.MULTIPLE_SELECT:
                if not selected_opt_ids:
                    db_ans.marksAwarded = 0.0
                    db_ans.isCorrect = Correctness.INCORRECT
                    db_ans.gradingStatus = GradingStatus.AUTO_GRADED
                else:
                    wrong_selected = selected_opt_ids - correct_opt_ids
                    right_selected = selected_opt_ids & correct_opt_ids
                    c_count = len(correct_opt_ids)

                    if wrong_selected:
                        # At least 1 wrong option selected
                        db_ans.marksAwarded = -penalty
                        db_ans.isCorrect = Correctness.INCORRECT
                        db_ans.gradingStatus = GradingStatus.AUTO_GRADED
                        total_marks_obtained -= penalty
                    elif selected_opt_ids == correct_opt_ids:
                        # All correct and none wrong
                        db_ans.marksAwarded = q_marks
                        db_ans.isCorrect = Correctness.FULLY_CORRECT
                        db_ans.gradingStatus = GradingStatus.AUTO_GRADED
                        total_marks_obtained += q_marks
                    elif right_selected and c_count > 0:
                        # Partial subset of correct options with 0 wrong options
                        partial_marks = round(
                            (len(right_selected) / c_count) * q_marks, 2
                        )
                        db_ans.marksAwarded = partial_marks
                        db_ans.isCorrect = Correctness.PARTIALLY_CORRECT
                        db_ans.gradingStatus = GradingStatus.AUTO_GRADED
                        total_marks_obtained += partial_marks
                    else:
                        db_ans.marksAwarded = 0.0
                        db_ans.isCorrect = Correctness.INCORRECT
                        db_ans.gradingStatus = GradingStatus.AUTO_GRADED

            elif db_ans.questionType in (
                QuestionType.SHORT_ANSWER,
                QuestionType.ESSAY,
            ):
                has_pending_subjective = True
                db_ans.gradingStatus = GradingStatus.PENDING

        db_attempt.marksObtained = max(0.0, round(total_marks_obtained, 2))
        db_attempt.submittedAt = datetime.now(UTC)
        db_attempt.status = (
            AttemptStatus.SUBMITTED if has_pending_subjective else AttemptStatus.GRADED
        )

        await s.commit()

        res_stmt = (
            select(StudentExam)
            .where(StudentExam.id == submit_data.id)
            .options(*STUDENT_EXAM_OPTIONS)
        )
        updated = (await s.execute(res_stmt)).scalar_one()
        resp = StudentExamResponse.model_validate(updated)
        resp.isResultsReleased = (
            updated.exam.isResultsReleased if updated.exam else False
        )
        return resp

    if session:
        return await _do_submit(session)
    async with db.get_session() as s:
        return await _do_submit(s)


async def get_student_exam_history(
    student_id: str, session: AsyncSession | None = None
) -> list[dict]:
    """Get all exam attempts for a student with exam details, scores, and percentages."""

    async def _do_get(s: AsyncSession):
        stmt = (
            select(StudentExam)
            .where(StudentExam.studentId == student_id)
            .options(selectinload(StudentExam.exam))
            .order_by(StudentExam.startedAt.desc())
        )
        results = (await s.execute(stmt)).scalars().all()
        items = []
        for se in results:
            exam = se.exam
            max_marks = exam.maxMarks if exam and exam.maxMarks > 0 else 1
            items.append(
                {
                    "id": se.id,
                    "examId": exam.id if exam else se.examId,
                    "examTitle": exam.name if exam else "Unknown Exam",
                    "examCode": exam.examCode if exam else "",
                    "subject": (
                        exam.subject.value
                        if exam
                        and exam.subject is not None
                        and hasattr(exam.subject, "value")
                        else (exam.subject if exam else None)
                    ),
                    "examType": (
                        exam.type.value
                        if exam and hasattr(exam.type, "value")
                        else (exam.type if exam else "EXAM")
                    ),
                    "scheduledAt": exam.scheduledAt if exam else se.startedAt,
                    "submittedAt": se.submittedAt,
                    "status": (
                        se.status.value
                        if hasattr(se.status, "value")
                        else str(se.status)
                    ),
                    "marksObtained": se.marksObtained,
                    "maxMarks": exam.maxMarks if exam else 0,
                    "percentage": round((se.marksObtained / max_marks) * 100, 2),
                    "isResultsReleased": exam.isResultsReleased if exam else False,
                }
            )
        return items

    if session:
        return await _do_get(session)
    async with db.get_session() as s:
        return await _do_get(s)
