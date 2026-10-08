"""Functional and integration tests for Teacher Results Analytics endpoints and services."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    Correctness,
    GradingStatus,
    QuestionType,
    Role,
    StudentExamStatus,
    Subject,
)
from tests.factories.attempt_factory import (
    create_attempt_answer_factory,
    create_attempt_factory,
)
from tests.factories.class_factory import create_class_factory
from tests.factories.exam_factory import (
    create_exam_factory,
    create_question_factory,
)
from tests.factories.school_factory import create_school_factory
from tests.factories.student_factory import create_student_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory


@pytest.mark.asyncio
async def test_teacher_results_overview_scoped_to_teacher(
    auth_client_factory, db_session: AsyncSession
):
    """Verify teacher results overview calculates correct metrics strictly scoped to teacher's exams."""
    school = await create_school_factory(db_session, school_code="SCH-OV1")
    teacher1_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="t1.overview@test.examarena.dev"
    )
    teacher1 = await create_teacher_factory(
        db_session, user=teacher1_user, school=school
    )

    teacher2_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="t2.overview@test.examarena.dev"
    )
    teacher2 = await create_teacher_factory(
        db_session, user=teacher2_user, school=school
    )

    school_class = await create_class_factory(
        db_session, school=school, teacher=teacher1
    )
    student1_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="s1.overview@test.examarena.dev"
    )
    student1 = await create_student_factory(
        db_session, user=student1_user, school=school, school_class=school_class
    )

    # Teacher 1 exams: 2 exams
    exam1 = await create_exam_factory(
        db_session, teacher=teacher1, max_marks=100, is_published=True
    )
    exam2 = await create_exam_factory(
        db_session, teacher=teacher1, max_marks=100, is_published=True
    )

    # Attempts on Teacher 1 exams:
    # 1 GRADED attempt (80/100 = 80%)
    await create_attempt_factory(
        db_session,
        exam=exam1,
        student=student1,
        status=StudentExamStatus.GRADED,
        marks_obtained=80.0,
        submitted_at=datetime.now(UTC),
    )
    # 1 SUBMITTED attempt (60/100 = 60%)
    await create_attempt_factory(
        db_session,
        exam=exam2,
        student=student1,
        status=StudentExamStatus.SUBMITTED,
        marks_obtained=60.0,
        submitted_at=datetime.now(UTC),
    )

    # Teacher 2 exam (must not leak into Teacher 1 overview)
    exam_t2 = await create_exam_factory(
        db_session, teacher=teacher2, max_marks=100, is_published=True
    )
    await create_attempt_factory(
        db_session,
        exam=exam_t2,
        student=student1,
        status=StudentExamStatus.GRADED,
        marks_obtained=100.0,
        submitted_at=datetime.now(UTC),
    )
    await db_session.commit()

    client = await auth_client_factory(teacher1_user)
    resp = await client.get("/api/v1/teacher/results/overview")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["totalExams"] == 2
    assert data["totalAttempts"] == 2
    assert data["gradedAttempts"] == 1
    assert data["pendingGradingAttempts"] == 1
    # Average of 80% and 60% = 70.0%
    assert data["averagePercentage"] == 70.0
    assert data["classes"] >= 1


@pytest.mark.asyncio
async def test_principal_results_overview_includes_entire_school(
    auth_client_factory, db_session: AsyncSession
):
    """Verify principal results overview aggregates all teachers within their school."""
    from app.core.models import Principal

    school_a = await create_school_factory(db_session, school_code="SCH-PRIN-A")
    school_b = await create_school_factory(db_session, school_code="SCH-PRIN-B")

    principal_user = await create_user_factory(
        db_session, role=Role.PRINCIPAL, email="principal.a@test.examarena.dev"
    )
    principal_teacher = await create_teacher_factory(
        db_session, user=principal_user, school=school_a
    )
    principal_record = Principal(
        teacherId=principal_teacher.id,
        schoolId=school_a.id,
        experience=10,
    )
    db_session.add(principal_record)
    await db_session.flush()

    t1_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="t1.prin@test.examarena.dev"
    )
    teacher_a = await create_teacher_factory(db_session, user=t1_user, school=school_a)

    t_b_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="tb.prin@test.examarena.dev"
    )
    teacher_b = await create_teacher_factory(db_session, user=t_b_user, school=school_b)

    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="stud.prin@test.examarena.dev"
    )
    student = await create_student_factory(
        db_session, user=student_user, school=school_a
    )

    # Exam in School A
    exam_a = await create_exam_factory(db_session, teacher=teacher_a, max_marks=100)
    await create_attempt_factory(
        db_session,
        exam=exam_a,
        student=student,
        status=StudentExamStatus.GRADED,
        marks_obtained=75.0,
        submitted_at=datetime.now(UTC),
    )

    # Exam in School B (must NOT be counted)
    exam_b = await create_exam_factory(db_session, teacher=teacher_b, max_marks=100)
    await create_attempt_factory(
        db_session,
        exam=exam_b,
        student=student,
        status=StudentExamStatus.GRADED,
        marks_obtained=95.0,
        submitted_at=datetime.now(UTC),
    )
    await db_session.commit()

    client = await auth_client_factory(principal_user)
    resp = await client.get("/api/v1/teacher/results/overview")
    assert resp.status_code == 200
    data = resp.json()

    assert data["totalExams"] == 1
    assert data["totalAttempts"] == 1
    assert data["gradedAttempts"] == 1
    assert data["averagePercentage"] == 75.0


@pytest.mark.asyncio
async def test_class_analytics_with_exam_performance_breakdown(
    auth_client_factory, db_session: AsyncSession
):
    """Verify class analytics calculates student counts, pass rates, and exam rows with grading workload."""
    school = await create_school_factory(db_session, school_code="SCH-CLS-AN")
    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="teacher.cls@test.examarena.dev"
    )
    teacher = await create_teacher_factory(
        db_session, user=teacher_user, school=school
    )
    school_class = await create_class_factory(
        db_session, school=school, teacher=teacher, name="Class 10A"
    )

    # Create 3 students in this class
    students = []
    for i in range(1, 4):
        u = await create_user_factory(
            db_session,
            role=Role.STUDENT,
            email=f"student{i}.cls@test.examarena.dev",
            name=f"Student {i}",
        )
        s = await create_student_factory(
            db_session,
            user=u,
            school=school,
            school_class=school_class,
            roll_no=f"R00{i}",
        )
        students.append(s)

    # Exam 1 (Science, maxMarks=100): 3 attempts, all graded
    exam1 = await create_exam_factory(
        db_session,
        teacher=teacher,
        name="Science Midterm",
        subject=Subject.SCIENCE,
        max_marks=100,
        is_published=True,
    )
    # Student 1: 90% (Pass), Student 2: 70% (Pass), Student 3: 30% (Fail)
    await create_attempt_factory(
        db_session,
        exam=exam1,
        student=students[0],
        status=StudentExamStatus.GRADED,
        marks_obtained=90.0,
        submitted_at=datetime.now(UTC),
    )
    await create_attempt_factory(
        db_session,
        exam=exam1,
        student=students[1],
        status=StudentExamStatus.GRADED,
        marks_obtained=70.0,
        submitted_at=datetime.now(UTC),
    )
    await create_attempt_factory(
        db_session,
        exam=exam1,
        student=students[2],
        status=StudentExamStatus.GRADED,
        marks_obtained=30.0,
        submitted_at=datetime.now(UTC),
    )

    # Exam 2 (Maths, maxMarks=50): 2 attempts, 1 graded, 1 submitted
    exam2 = await create_exam_factory(
        db_session,
        teacher=teacher,
        name="Maths Quiz",
        subject=Subject.MATHS,
        max_marks=50,
        is_published=True,
    )
    # Student 1: 40/50 = 80% (Graded)
    await create_attempt_factory(
        db_session,
        exam=exam2,
        student=students[0],
        status=StudentExamStatus.GRADED,
        marks_obtained=40.0,
        submitted_at=datetime.now(UTC),
    )
    # Student 2: 25/50 = 50% (Submitted)
    att2 = await create_attempt_factory(
        db_session,
        exam=exam2,
        student=students[1],
        status=StudentExamStatus.SUBMITTED,
        marks_obtained=25.0,
        submitted_at=datetime.now(UTC),
    )
    # Add a subjective question and pending answer to Exam 2
    q_sub = await create_question_factory(
        db_session,
        exam=exam2,
        question_type=QuestionType.SHORT_ANSWER,
        text="Explain calculus basics.",
        marks=10.0,
    )
    await create_attempt_answer_factory(
        db_session,
        attempt=att2,
        question=q_sub,
        text_answer="Calculus deals with rates of change.",
        grading_status=GradingStatus.PENDING,
    )
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    resp = await client.get(f"/api/v1/classes/{school_class.id}/analytics")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    summary = data["summary"]
    assert summary["classId"] == school_class.id
    assert summary["className"] == "Class 10A"
    assert summary["totalStudents"] == 3
    assert summary["totalExams"] == 2
    assert summary["totalAttempts"] == 5
    assert summary["gradedAttempts"] == 4
    assert summary["pendingGradingAttempts"] == 1
    # 4 passed out of 5 attempts: 90%, 70%, 30% (fail), 80%, 50% -> 4/5 = 80.0%
    assert summary["passRate"] == 80.0
    # grading completion: 4 / 5 = 80.0%
    assert summary["gradingCompletionRate"] == 80.0

    exams = data["exams"]
    assert len(exams) == 2
    sci_exam = next(e for e in exams if e["examTitle"] == "Science Midterm")
    assert sci_exam["studentsAttempted"] == 3
    assert sci_exam["highestPercentage"] == 90.0
    assert sci_exam["lowestPercentage"] == 30.0
    assert sci_exam["averagePercentage"] == 63.33
    assert sci_exam["passRate"] == 66.67
    assert sci_exam["pendingSubjectiveCount"] == 0

    math_exam = next(e for e in exams if e["examTitle"] == "Maths Quiz")
    assert math_exam["studentsAttempted"] == 2
    assert math_exam["pendingSubjectiveCount"] == 1


@pytest.mark.asyncio
async def test_class_leaderboard_normalized_percentages_and_deterministic_ties(
    auth_client_factory, db_session: AsyncSession
):
    """Verify class leaderboard calculates multi-exam ranking using normalized percentages, not raw sum marks."""
    school = await create_school_factory(db_session, school_code="SCH-LEAD-01")
    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="t.lead@test.examarena.dev"
    )
    teacher = await create_teacher_factory(
        db_session, user=teacher_user, school=school
    )
    school_class = await create_class_factory(
        db_session, school=school, teacher=teacher
    )

    # 3 Students: Alice, Bob, Charlie
    u_alice = await create_user_factory(
        db_session, role=Role.STUDENT, name="Alice", email="alice@test.dev"
    )
    s_alice = await create_student_factory(
        db_session,
        user=u_alice,
        school=school,
        school_class=school_class,
        roll_no="01",
    )

    u_bob = await create_user_factory(
        db_session, role=Role.STUDENT, name="Bob", email="bob@test.dev"
    )
    s_bob = await create_student_factory(
        db_session,
        user=u_bob,
        school=school,
        school_class=school_class,
        roll_no="02",
    )

    u_charlie = await create_user_factory(
        db_session, role=Role.STUDENT, name="Charlie", email="charlie@test.dev"
    )
    s_charlie = await create_student_factory(
        db_session,
        user=u_charlie,
        school=school,
        school_class=school_class,
        roll_no="03",
    )

    # Exam 1: maxMarks = 100
    exam1 = await create_exam_factory(
        db_session, teacher=teacher, max_marks=100, name="Exam 1"
    )
    # Exam 2: maxMarks = 20
    exam2 = await create_exam_factory(
        db_session, teacher=teacher, max_marks=20, name="Exam 2"
    )

    # Alice: Exam 1 = 90/100 (90%), Exam 2 = 18/20 (90%) -> avg = 90.0%
    await create_attempt_factory(
        db_session,
        exam=exam1,
        student=s_alice,
        status=StudentExamStatus.GRADED,
        marks_obtained=90.0,
        submitted_at=datetime.now(UTC),
    )
    await create_attempt_factory(
        db_session,
        exam=exam2,
        student=s_alice,
        status=StudentExamStatus.GRADED,
        marks_obtained=18.0,
        submitted_at=datetime.now(UTC),
    )

    # Bob: Exam 1 = 80/100 (80%), Exam 2 = 16/20 (80%) -> avg = 80.0%
    await create_attempt_factory(
        db_session,
        exam=exam1,
        student=s_bob,
        status=StudentExamStatus.GRADED,
        marks_obtained=80.0,
        submitted_at=datetime.now(UTC),
    )
    await create_attempt_factory(
        db_session,
        exam=exam2,
        student=s_bob,
        status=StudentExamStatus.GRADED,
        marks_obtained=16.0,
        submitted_at=datetime.now(UTC),
    )

    # Charlie: Exam 1 = 80/100 (80%), Exam 2 = 16/20 (80%) -> avg = 80.0% (Tied with Bob)
    await create_attempt_factory(
        db_session,
        exam=exam1,
        student=s_charlie,
        status=StudentExamStatus.GRADED,
        marks_obtained=80.0,
        submitted_at=datetime.now(UTC),
    )
    await create_attempt_factory(
        db_session,
        exam=exam2,
        student=s_charlie,
        status=StudentExamStatus.GRADED,
        marks_obtained=16.0,
        submitted_at=datetime.now(UTC),
    )
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    resp = await client.get(f"/api/v1/classes/{school_class.id}/leaderboard")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    board = data["leaderboard"]
    assert len(board) == 3
    # Rank 1: Alice (90.0%)
    assert board[0]["studentName"] == "Alice"
    assert board[0]["rank"] == 1
    assert board[0]["averagePercentage"] == 90.0

    # Tied ranks between Bob and Charlie (80.0%):
    # Deterministic tie break by rollNo: "02" (Bob) comes before "03" (Charlie)
    assert board[1]["studentName"] == "Bob"
    assert board[1]["rank"] == 2
    assert board[1]["averagePercentage"] == 80.0

    assert board[2]["studentName"] == "Charlie"
    assert board[2]["rank"] == 3
    assert board[2]["averagePercentage"] == 80.0


@pytest.mark.asyncio
async def test_student_results_and_history_for_teacher(
    auth_client_factory, db_session: AsyncSession
):
    """Verify teacher can retrieve student exam history and summary, distinguishing SUBMITTED from GRADED."""
    school = await create_school_factory(db_session, school_code="SCH-ST-RES")
    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="t.studentres@test.dev"
    )
    teacher = await create_teacher_factory(
        db_session, user=teacher_user, school=school
    )
    school_class = await create_class_factory(
        db_session, school=school, teacher=teacher
    )

    stud_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="stud.single@test.dev", name="David"
    )
    student = await create_student_factory(
        db_session,
        user=stud_user,
        school=school,
        school_class=school_class,
        roll_no="42",
    )

    exam1 = await create_exam_factory(
        db_session, teacher=teacher, name="Biology 101", max_marks=100
    )
    exam2 = await create_exam_factory(
        db_session, teacher=teacher, name="Chemistry 101", max_marks=100
    )

    # 1 GRADED attempt (85/100) -> counted in performance summary
    await create_attempt_factory(
        db_session,
        exam=exam1,
        student=student,
        status=StudentExamStatus.GRADED,
        marks_obtained=85.0,
        submitted_at=datetime.now(UTC),
    )
    # 1 SUBMITTED attempt (pending grading) -> NOT counted as finalized score
    await create_attempt_factory(
        db_session,
        exam=exam2,
        student=student,
        status=StudentExamStatus.SUBMITTED,
        marks_obtained=40.0,
        submitted_at=datetime.now(UTC),
    )
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    resp = await client.get(f"/api/v1/students/{student.id}/results")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    summary = data["summary"]
    # Total attempted exams is 2 (1 finalized, 1 pending grading)
    assert summary["totalExams"] == 2
    assert summary["averagePercentage"] == 85.0
    assert summary["highestPercentage"] == 85.0
    assert summary["lowestPercentage"] == 85.0
    assert summary["passed"] == 1
    assert summary["failed"] == 0
    assert summary["pendingSubjectiveGradingExams"] == 1

    history = data["history"]
    assert len(history) == 2
    statuses = {h["status"] for h in history}
    assert "GRADED" in statuses
    assert "SUBMITTED" in statuses


@pytest.mark.asyncio
async def test_exam_analytics_detail_and_deterministic_ties(
    auth_client_factory, db_session: AsyncSession
):
    """Verify exam analytics returns detailed workload, statistics, and deterministic scoreboard."""
    school = await create_school_factory(db_session, school_code="SCH-EX-AN")
    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="t.examanalytics@test.dev"
    )
    teacher = await create_teacher_factory(
        db_session, user=teacher_user, school=school
    )

    school_class = await create_class_factory(
        db_session, school=school, teacher=teacher
    )

    u1 = await create_user_factory(
        db_session, role=Role.STUDENT, name="Student Alpha", email="alpha@test.dev"
    )
    s1 = await create_student_factory(
        db_session, user=u1, school=school, school_class=school_class, roll_no="101"
    )
    u2 = await create_user_factory(
        db_session, role=Role.STUDENT, name="Student Beta", email="beta@test.dev"
    )
    s2 = await create_student_factory(
        db_session, user=u2, school=school, school_class=school_class, roll_no="102"
    )

    exam = await create_exam_factory(
        db_session, teacher=teacher, name="Final Exam", max_marks=100
    )

    # Identical score (75.0)
    att1 = await create_attempt_factory(
        db_session,
        exam=exam,
        student=s1,
        status=StudentExamStatus.GRADED,
        marks_obtained=75.0,
        submitted_at=datetime.now(UTC),
    )
    att2 = await create_attempt_factory(
        db_session,
        exam=exam,
        student=s2,
        status=StudentExamStatus.GRADED,
        marks_obtained=75.0,
        submitted_at=datetime.now(UTC),
    )
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    resp = await client.get(f"/api/v1/exams/{exam.id}/analytics")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["examId"] == exam.id
    assert data["totalAttempts"] == 2
    assert data["gradedAttempts"] == 2
    assert data["averagePercentage"] == 75.0
    assert data["passRate"] == 100.0

    # Ranks must be assigned 1 and 2 deterministically
    lb = data["leaderboard"]
    assert len(lb) == 2
    assert lb[0]["rank"] == 1
    assert lb[1]["rank"] == 2
    assert lb[0]["marksObtained"] == 75.0
    assert lb[1]["marksObtained"] == 75.0
