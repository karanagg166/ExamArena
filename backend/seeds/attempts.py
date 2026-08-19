"""Student exam attempts, submission grading, and selected options seeding module."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    Correctness,
    Exam,
    GradingStatus,
    Question,
    QuestionOption,
    QuestionType,
    SelectedOption,
    Student,
    StudentExam,
    StudentExamAnswer,
    StudentExamStatus,
    User,
)


async def get_question_options(
    session: AsyncSession, question_id: str
) -> list[QuestionOption]:
    """Retrieve options for a given question."""
    stmt = select(QuestionOption).where(QuestionOption.questionId == question_id)
    return (await session.execute(stmt)).scalars().all()


async def seed_student_attempts(
    session: AsyncSession,
    exams_map: dict[str, Exam],
    students_map: dict[str, tuple[User, Student]],
) -> None:
    """Seed realistic student attempts with varying performance across exams."""
    print("\n📊 Generating Realistic Student Attempts...", flush=True)

    exam1 = exams_map["exam1"]
    exam2 = exams_map["exam2"]
    exam3 = exams_map["exam3"]

    e1_qs = (
        (
            await session.execute(
                select(Question)
                .where(Question.examId == exam1.id)
                .order_by(Question.questionNumber)
            )
        )
        .scalars()
        .all()
    )
    e2_qs = (
        (
            await session.execute(
                select(Question)
                .where(Question.examId == exam2.id)
                .order_by(Question.questionNumber)
            )
        )
        .scalars()
        .all()
    )
    e3_qs = (
        (
            await session.execute(
                select(Question)
                .where(Question.examId == exam3.id)
                .order_by(Question.questionNumber)
            )
        )
        .scalars()
        .all()
    )

    # 1. Alex Morgan (student@gmail.com) on Exam 1 -> 28/30 (Rank 1)
    alex_st = students_map["student@gmail.com"][1]
    if not (
        await session.execute(
            select(StudentExam).where(
                StudentExam.studentId == alex_st.id, StudentExam.examId == exam1.id
            )
        )
    ).scalar_one_or_none():
        att1 = StudentExam(
            studentId=alex_st.id,
            examId=exam1.id,
            marksObtained=28.0,
            startedAt=datetime.now(UTC) - timedelta(days=5, minutes=50),
            submittedAt=datetime.now(UTC) - timedelta(days=5, minutes=12),
            status=StudentExamStatus.GRADED,
        )
        session.add(att1)
        await session.commit()
        await session.refresh(att1)

        for q in e1_qs:
            opts = await get_question_options(session, q.id)
            corr_opt = next((o for o in opts if o.isCorrect), None)
            if q.questionType in (
                QuestionType.MULTIPLE_CHOICE,
                QuestionType.TRUE_FALSE,
            ):
                ans = StudentExamAnswer(
                    studentExamId=att1.id,
                    questionId=q.id,
                    questionType=q.questionType,
                    marksAwarded=float(q.marks),
                    isCorrect=Correctness.FULLY_CORRECT,
                    gradingStatus=GradingStatus.AUTO_GRADED,
                    feedback="Correct answer.",
                )
                session.add(ans)
                await session.commit()
                await session.refresh(ans)
                if corr_opt:
                    session.add(
                        SelectedOption(studentExamAnswerId=ans.id, optionId=corr_opt.id)
                    )
            elif q.questionNumber == 9:
                session.add(
                    StudentExamAnswer(
                        studentExamId=att1.id,
                        questionId=q.id,
                        questionType=QuestionType.SHORT_ANSWER,
                        textAnswer="Speed is a scalar quantity indicating how fast an object moves, whereas velocity is a vector that includes speed and direction. For example, a car traveling 80 km/h East reaches a specific destination, but 80 km/h West moves directly away from it.",
                        marksAwarded=7.0,
                        isCorrect=Correctness.FULLY_CORRECT,
                        gradingStatus=GradingStatus.MANUALLY_GRADED,
                        feedback="Excellent conceptual clarity and precise real-world example.",
                    )
                )
            elif q.questionNumber == 10:
                session.add(
                    StudentExamAnswer(
                        studentExamId=att1.id,
                        questionId=q.id,
                        questionType=QuestionType.SHORT_ANSWER,
                        textAnswer="Boyle's Law states that at constant temperature, the absolute pressure exerted by a given mass of gas is inversely proportional to its volume. Equation: P1 * V1 = P2 * V2.",
                        marksAwarded=5.0,
                        isCorrect=Correctness.PARTIALLY_CORRECT,
                        gradingStatus=GradingStatus.MANUALLY_GRADED,
                        feedback="Good formulation; remember to explicitly mention ideal gas behavior.",
                    )
                )
        await session.commit()
        print(
            "  [+] Recorded Attempt: student@gmail.com on Exam 1 -> 28/30 (Rank 1)",
            flush=True,
        )

    # 2. Emma Watson (emma.student@gmail.com) on Exam 1 -> 23/30 (Rank 2)
    emma_st = students_map["emma.student@gmail.com"][1]
    if not (
        await session.execute(
            select(StudentExam).where(
                StudentExam.studentId == emma_st.id, StudentExam.examId == exam1.id
            )
        )
    ).scalar_one_or_none():
        att2 = StudentExam(
            studentId=emma_st.id,
            examId=exam1.id,
            marksObtained=23.0,
            startedAt=datetime.now(UTC) - timedelta(days=5, minutes=48),
            submittedAt=datetime.now(UTC) - timedelta(days=5, minutes=6),
            status=StudentExamStatus.GRADED,
        )
        session.add(att2)
        await session.commit()
        await session.refresh(att2)

        for q in e1_qs:
            opts = await get_question_options(session, q.id)
            corr_opt = next((o for o in opts if o.isCorrect), None)
            wrong_opt = next((o for o in opts if not o.isCorrect), None)
            if q.questionNumber == 3:
                ans = StudentExamAnswer(
                    studentExamId=att2.id,
                    questionId=q.id,
                    questionType=q.questionType,
                    marksAwarded=0.0,
                    isCorrect=Correctness.INCORRECT,
                    gradingStatus=GradingStatus.AUTO_GRADED,
                    feedback="Incorrect. Fluorine has the highest electronegativity.",
                )
                session.add(ans)
                await session.commit()
                await session.refresh(ans)
                if wrong_opt:
                    session.add(
                        SelectedOption(
                            studentExamAnswerId=ans.id, optionId=wrong_opt.id
                        )
                    )
            elif q.questionType in (
                QuestionType.MULTIPLE_CHOICE,
                QuestionType.TRUE_FALSE,
            ):
                ans = StudentExamAnswer(
                    studentExamId=att2.id,
                    questionId=q.id,
                    questionType=q.questionType,
                    marksAwarded=float(q.marks),
                    isCorrect=Correctness.FULLY_CORRECT,
                    gradingStatus=GradingStatus.AUTO_GRADED,
                )
                session.add(ans)
                await session.commit()
                await session.refresh(ans)
                if corr_opt:
                    session.add(
                        SelectedOption(studentExamAnswerId=ans.id, optionId=corr_opt.id)
                    )
            elif q.questionNumber == 9:
                session.add(
                    StudentExamAnswer(
                        studentExamId=att2.id,
                        questionId=q.id,
                        questionType=QuestionType.SHORT_ANSWER,
                        textAnswer="Speed is scalar and velocity has direction. For instance, planes need velocity to follow flight plans.",
                        marksAwarded=5.0,
                        isCorrect=Correctness.PARTIALLY_CORRECT,
                        gradingStatus=GradingStatus.MANUALLY_GRADED,
                        feedback="Accurate summary, include formal definitions next time.",
                    )
                )
            elif q.questionNumber == 10:
                session.add(
                    StudentExamAnswer(
                        studentExamId=att2.id,
                        questionId=q.id,
                        questionType=QuestionType.SHORT_ANSWER,
                        textAnswer="Pressure is inversely proportional to volume when temperature is kept constant.",
                        marksAwarded=4.0,
                        isCorrect=Correctness.PARTIALLY_CORRECT,
                        gradingStatus=GradingStatus.MANUALLY_GRADED,
                        feedback="Please include algebraic equation P1V1=P2V2.",
                    )
                )
        await session.commit()
        print(
            "  [+] Recorded Attempt: emma.student@gmail.com on Exam 1 -> 23/30 (Rank 2)",
            flush=True,
        )

    # 3. Liam Davies (liam.student@gmail.com) on Exam 2 -> 35/35 (100%)
    liam_st = students_map["liam.student@gmail.com"][1]
    if not (
        await session.execute(
            select(StudentExam).where(
                StudentExam.studentId == liam_st.id, StudentExam.examId == exam2.id
            )
        )
    ).scalar_one_or_none():
        att3 = StudentExam(
            studentId=liam_st.id,
            examId=exam2.id,
            marksObtained=35.0,
            startedAt=datetime.now(UTC) - timedelta(days=3, minutes=58),
            submittedAt=datetime.now(UTC) - timedelta(days=3, minutes=6),
            status=StudentExamStatus.GRADED,
        )
        session.add(att3)
        await session.commit()
        await session.refresh(att3)

        for q in e2_qs:
            opts = await get_question_options(session, q.id)
            corr_opts = [o for o in opts if o.isCorrect]
            if q.questionType in (
                QuestionType.MULTIPLE_CHOICE,
                QuestionType.MULTIPLE_SELECT,
            ):
                ans = StudentExamAnswer(
                    studentExamId=att3.id,
                    questionId=q.id,
                    questionType=q.questionType,
                    marksAwarded=float(q.marks),
                    isCorrect=Correctness.FULLY_CORRECT,
                    gradingStatus=GradingStatus.AUTO_GRADED,
                    feedback="Perfect solution.",
                )
                session.add(ans)
                await session.commit()
                await session.refresh(ans)
                for c_opt in corr_opts:
                    session.add(
                        SelectedOption(studentExamAnswerId=ans.id, optionId=c_opt.id)
                    )
            elif q.questionNumber == 8:
                session.add(
                    StudentExamAnswer(
                        studentExamId=att3.id,
                        questionId=q.id,
                        questionType=QuestionType.SHORT_ANSWER,
                        textAnswer="f'(x) = 4x - 8. Setting f'(x) = 0 gives x = 2. Calculating second derivative: f''(x) = 4 > 0 (concave upwards), proving (2, -2) is a local minimum.",
                        marksAwarded=10.0,
                        isCorrect=Correctness.FULLY_CORRECT,
                        gradingStatus=GradingStatus.MANUALLY_GRADED,
                        feedback="Outstanding and rigorous calculus derivation.",
                    )
                )
        await session.commit()
        print(
            "  [+] Recorded Attempt: liam.student@gmail.com on Exam 2 -> 35/35 (100%)",
            flush=True,
        )

    # 4. Sophia Chen (sophia.student@gmail.com) on Exam 2 -> 29/35
    sophia_st = students_map["sophia.student@gmail.com"][1]
    if not (
        await session.execute(
            select(StudentExam).where(
                StudentExam.studentId == sophia_st.id, StudentExam.examId == exam2.id
            )
        )
    ).scalar_one_or_none():
        att4 = StudentExam(
            studentId=sophia_st.id,
            examId=exam2.id,
            marksObtained=29.0,
            startedAt=datetime.now(UTC) - timedelta(days=3, minutes=55),
            submittedAt=datetime.now(UTC) - timedelta(days=3, minutes=4),
            status=StudentExamStatus.GRADED,
        )
        session.add(att4)
        await session.commit()
        await session.refresh(att4)

        for q in e2_qs:
            opts = await get_question_options(session, q.id)
            corr_opts = [o for o in opts if o.isCorrect]
            wrong_opt = next((o for o in opts if not o.isCorrect), None)
            if q.questionNumber == 5:
                ans = StudentExamAnswer(
                    studentExamId=att4.id,
                    questionId=q.id,
                    questionType=q.questionType,
                    marksAwarded=0.0,
                    isCorrect=Correctness.INCORRECT,
                    gradingStatus=GradingStatus.AUTO_GRADED,
                    feedback="Incorrect integral coefficient.",
                )
                session.add(ans)
                await session.commit()
                await session.refresh(ans)
                if wrong_opt:
                    session.add(
                        SelectedOption(
                            studentExamAnswerId=ans.id, optionId=wrong_opt.id
                        )
                    )
            elif q.questionType in (
                QuestionType.MULTIPLE_CHOICE,
                QuestionType.MULTIPLE_SELECT,
            ):
                ans = StudentExamAnswer(
                    studentExamId=att4.id,
                    questionId=q.id,
                    questionType=q.questionType,
                    marksAwarded=float(q.marks),
                    isCorrect=Correctness.FULLY_CORRECT,
                    gradingStatus=GradingStatus.AUTO_GRADED,
                )
                session.add(ans)
                await session.commit()
                await session.refresh(ans)
                for c_opt in corr_opts:
                    session.add(
                        SelectedOption(studentExamAnswerId=ans.id, optionId=c_opt.id)
                    )
            elif q.questionNumber == 8:
                session.add(
                    StudentExamAnswer(
                        studentExamId=att4.id,
                        questionId=q.id,
                        questionType=QuestionType.SHORT_ANSWER,
                        textAnswer="Derivative is 4x - 8 = 0 => x = 2. Value at x=2 is 2(4) - 16 + 6 = -2. The point is (2, -2) and it is a minimum.",
                        marksAwarded=9.0,
                        isCorrect=Correctness.PARTIALLY_CORRECT,
                        gradingStatus=GradingStatus.MANUALLY_GRADED,
                        feedback="Very good calculation. Always explicitly state the second derivative test.",
                    )
                )
        await session.commit()
        print(
            "  [+] Recorded Attempt: sophia.student@gmail.com on Exam 2 -> 29/35",
            flush=True,
        )

    # 5. Alex Morgan on Exam 3 (Active Quiz) -> 10/10 Submitted
    if not (
        await session.execute(
            select(StudentExam).where(
                StudentExam.studentId == alex_st.id, StudentExam.examId == exam3.id
            )
        )
    ).scalar_one_or_none():
        att5 = StudentExam(
            studentId=alex_st.id,
            examId=exam3.id,
            marksObtained=10.0,
            startedAt=datetime.now(UTC) - timedelta(hours=1, minutes=20),
            submittedAt=datetime.now(UTC) - timedelta(hours=1, minutes=2),
            status=StudentExamStatus.SUBMITTED,
        )
        session.add(att5)
        await session.commit()
        await session.refresh(att5)

        for q in e3_qs:
            opts = await get_question_options(session, q.id)
            corr_opt = next((o for o in opts if o.isCorrect), None)
            ans = StudentExamAnswer(
                studentExamId=att5.id,
                questionId=q.id,
                questionType=q.questionType,
                marksAwarded=float(q.marks),
                isCorrect=Correctness.FULLY_CORRECT,
                gradingStatus=GradingStatus.AUTO_GRADED,
                feedback="Correct answer.",
            )
            session.add(ans)
            await session.commit()
            await session.refresh(ans)
            if corr_opt:
                session.add(
                    SelectedOption(studentExamAnswerId=ans.id, optionId=corr_opt.id)
                )
        await session.commit()
        print(
            "  [+] Recorded Submitted Attempt: student@gmail.com on Exam 3 -> 10/10 (Submitted)",
            flush=True,
        )
