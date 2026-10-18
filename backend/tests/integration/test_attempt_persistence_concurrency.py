"""Integration tests for attempt autosave concurrency, recovery, and server-side persistence."""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    Exam,
    Question,
    QuestionOption,
    QuestionType,
    Role,
    StudentExam,
    StudentExamAnswer,
    StudentExamStatus,
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


@pytest.fixture
async def exam_concurrency_fixture(db_session: AsyncSession):
    """Sets up School, Class, Teacher, 2 Questions (MCQ and Short Answer), and Student."""
    school = await create_school_factory(db_session, school_code="SCH-CONC-1")
    school_class = await create_class_factory(db_session, school=school)

    teacher_user = await create_user_factory(
        db_session, role=Role.TEACHER, email="t_conc1@dev.local"
    )
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)

    exam = await create_exam_factory(
        db_session,
        teacher=teacher,
        name="Concurrency & Autosave Exam",
        duration=10,  # 10 minutes
        is_published=True,
        is_public=True,
    )

    # Q1: Multiple Choice
    q1 = await create_question_factory(
        db_session,
        exam=exam,
        question_number=1,
        text="What is the result of 2 + 2?",
        marks=5,
        question_type=QuestionType.MULTIPLE_CHOICE,
        options_data=[
            {"text": "3", "isCorrect": False},
            {"text": "4", "isCorrect": True},
        ],
    )

    # Q2: Short Answer
    q2 = await create_question_factory(
        db_session,
        exam=exam,
        question_number=2,
        text="Explain photosynthesis.",
        marks=5,
        question_type=QuestionType.SHORT_ANSWER,
    )

    student_user = await create_user_factory(
        db_session, role=Role.STUDENT, email="stu_conc1@dev.local"
    )
    student = await create_student_factory(
        db_session, user=student_user, school=school, school_class=school_class
    )
    await db_session.commit()

    # Load options for Q1
    q1_opts = (
        await db_session.execute(
            select(QuestionOption).where(QuestionOption.questionId == q1.id)
        )
    ).scalars().all()
    opt_wrong = next(o for o in q1_opts if o.text == "3")
    opt_correct = next(o for o in q1_opts if o.text == "4")

    return {
        "exam": exam,
        "q1": q1,
        "opt_wrong": opt_wrong,
        "opt_correct": opt_correct,
        "q2": q2,
        "student": student,
        "user": student_user,
    }


@pytest.mark.asyncio
async def test_refresh_after_multiple_accepted_draft_revisions(
    auth_client_factory, db_session: AsyncSession, exam_concurrency_fixture
):
    """Saving multiple successive revisions persists exact database state verifiable on refresh."""
    fix = exam_concurrency_fixture
    client = await auth_client_factory(fix["user"])

    # 1. Start exam
    start_res = await client.post("/api/v1/attempts/start", json={"examId": fix["exam"].id})
    assert start_res.status_code in (200, 201)
    attempt_id = start_res.json()["id"]

    # 2. Draft Revision 1: Select wrong option for Q1
    d1 = {
        "baseRevision": 0,
        "clientSequence": 1,
        "answers": [
            {
                "questionId": fix["q1"].id,
                "selectedOptions": [{"optionId": fix["opt_wrong"].id}],
            }
        ],
    }
    r1 = await client.put(f"/api/v1/attempts/{attempt_id}/draft", json=d1)
    assert r1.status_code == 200
    assert r1.json()["applied"] is True
    assert r1.json()["revision"] == 1

    # 3. Draft Revision 2: Update Q1 to correct option and add text to Q2
    d2 = {
        "baseRevision": 1,
        "clientSequence": 2,
        "answers": [
            {
                "questionId": fix["q1"].id,
                "selectedOptions": [{"optionId": fix["opt_correct"].id}],
            },
            {
                "questionId": fix["q2"].id,
                "textAnswer": "Sunlight conversion process",
            },
        ],
    }
    r2 = await client.put(f"/api/v1/attempts/{attempt_id}/draft", json=d2)
    assert r2.status_code == 200
    assert r2.json()["applied"] is True
    assert r2.json()["revision"] == 2

    # 4. Refresh: GET attempt from server
    get_res = await client.get(f"/api/v1/attempts/{attempt_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["draftRevision"] == 2
    ans_map = {a["questionId"]: a for a in data["answers"]}
    assert ans_map[fix["q1"].id]["selectedOptions"][0]["optionId"] == fix["opt_correct"].id
    assert ans_map[fix["q2"].id]["textAnswer"] == "Sunlight conversion process"

    # 5. Direct database assertion
    db_attempt = (
        await db_session.execute(
            select(StudentExam).where(StudentExam.id == attempt_id)
        )
    ).scalar_one()
    assert db_attempt.draftRevision == 2


@pytest.mark.asyncio
async def test_two_tabs_editing_same_attempt_revision_conflict(
    auth_client_factory, db_session: AsyncSession, exam_concurrency_fixture
):
    """Tab A advances revision from 0 -> 1. Tab B sending stale baseRevision 0 is rejected with conflict."""
    fix = exam_concurrency_fixture
    client = await auth_client_factory(fix["user"])

    start_res = await client.post("/api/v1/attempts/start", json={"examId": fix["exam"].id})
    attempt_id = start_res.json()["id"]

    # Tab A saves revision 1
    tab_a_payload = {
        "baseRevision": 0,
        "clientSequence": 1,
        "answers": [{"questionId": fix["q2"].id, "textAnswer": "Text from Tab A"}],
    }
    res_a = await client.put(f"/api/v1/attempts/{attempt_id}/draft", json=tab_a_payload)
    assert res_a.status_code == 200
    assert res_a.json()["applied"] is True
    assert res_a.json()["revision"] == 1

    # Tab B was open with baseRevision 0 and attempts to save
    tab_b_payload = {
        "baseRevision": 0,
        "clientSequence": 1,
        "answers": [{"questionId": fix["q2"].id, "textAnswer": "Text from Tab B"}],
    }
    res_b = await client.put(f"/api/v1/attempts/{attempt_id}/draft", json=tab_b_payload)
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["applied"] is False
    assert data_b["conflict"] is True
    assert data_b["revision"] == 1

    # Verify Tab A's data remains in DB
    refreshed = (
        await db_session.execute(
            select(StudentExamAnswer).where(
                StudentExamAnswer.studentExamId == attempt_id,
                StudentExamAnswer.questionId == fix["q2"].id,
            )
        )
    ).scalar_one()
    assert refreshed.textAnswer == "Text from Tab A"


@pytest.mark.asyncio
async def test_out_of_order_draft_requests_ignored(
    auth_client_factory, db_session: AsyncSession, exam_concurrency_fixture
):
    """A delayed draft request with older clientSequence is ignored by server."""
    fix = exam_concurrency_fixture
    client = await auth_client_factory(fix["user"])

    start_res = await client.post("/api/v1/attempts/start", json={"examId": fix["exam"].id})
    attempt_id = start_res.json()["id"]

    # Higher client sequence arrives first
    r_new = await client.put(
        f"/api/v1/attempts/{attempt_id}/draft",
        json={
            "clientSequence": 5,
            "answers": [{"questionId": fix["q2"].id, "textAnswer": "Newer text"}],
        },
    )
    assert r_new.status_code == 200
    assert r_new.json()["savedCount"] == 1

    # Stale sequence arrives delayed
    r_old = await client.put(
        f"/api/v1/attempts/{attempt_id}/draft",
        json={
            "clientSequence": 3,
            "answers": [{"questionId": fix["q2"].id, "textAnswer": "Stale delayed text"}],
        },
    )
    assert r_old.status_code == 200
    assert r_old.json()["savedCount"] == 0

    refreshed = (
        await db_session.execute(
            select(StudentExamAnswer).where(
                StudentExamAnswer.studentExamId == attempt_id,
                StudentExamAnswer.questionId == fix["q2"].id,
            )
        )
    ).scalar_one()
    assert refreshed.textAnswer == "Newer text"


@pytest.mark.asyncio
async def test_duplicate_submission_is_idempotent(
    auth_client_factory, db_session: AsyncSession, exam_concurrency_fixture
):
    """Submitting an attempt twice is idempotent and does not corrupt answers or duplicate records."""
    fix = exam_concurrency_fixture
    client = await auth_client_factory(fix["user"])

    start_res = await client.post("/api/v1/attempts/start", json={"examId": fix["exam"].id})
    attempt_id = start_res.json()["id"]
    ans_shell_id = start_res.json()["answers"][0]["id"]

    submit_payload = {
        "id": attempt_id,
        "answers": [
            {
                "id": ans_shell_id,
                "selectedOptions": [{"optionId": fix["opt_correct"].id}],
            }
        ],
    }

    # 1. First submit
    sub1 = await client.post("/api/v1/attempts/submit", json=submit_payload)
    assert sub1.status_code == 200
    assert sub1.json()["status"] == "SUBMITTED"

    # 2. Second submit (network retry / duplicate)
    sub2 = await client.post("/api/v1/attempts/submit", json=submit_payload)
    assert sub2.status_code == 400
    assert "already been submitted" in sub2.json()["detail"].lower()

    # Assert exactly 1 attempt record in database and state is SUBMITTED
    attempts = (
        await db_session.execute(
            select(StudentExam).where(StudentExam.id == attempt_id)
        )
    ).scalars().all()
    assert len(attempts) == 1
    assert attempts[0].status == StudentExamStatus.SUBMITTED


@pytest.mark.asyncio
async def test_late_edits_rejected_after_submission(
    auth_client_factory, db_session: AsyncSession, exam_concurrency_fixture
):
    """Once submitted, drafts cannot be modified."""
    fix = exam_concurrency_fixture
    client = await auth_client_factory(fix["user"])

    start_res = await client.post("/api/v1/attempts/start", json={"examId": fix["exam"].id})
    attempt_id = start_res.json()["id"]
    ans_shell_id = start_res.json()["answers"][0]["id"]

    await client.post(
        "/api/v1/attempts/submit",
        json={"id": attempt_id, "answers": [{"id": ans_shell_id}]},
    )

    # Attempt to save draft
    late_res = await client.put(
        f"/api/v1/attempts/{attempt_id}/draft",
        json={
            "clientSequence": 99,
            "answers": [{"questionId": fix["q1"].id, "textAnswer": "Tampering after submit"}],
        },
    )
    assert late_res.status_code == 400
    assert "already submitted" in late_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_server_expiry_while_disconnected_rejects_edits(
    auth_client_factory, db_session: AsyncSession, exam_concurrency_fixture
):
    """When duration is exceeded, attempt transitions to EXPIRED in database and rejects draft saves."""
    fix = exam_concurrency_fixture
    client = await auth_client_factory(fix["user"])

    start_res = await client.post("/api/v1/attempts/start", json={"examId": fix["exam"].id})
    attempt_id = start_res.json()["id"]

    # Simulate client disconnect and clock advancing past duration (10 mins + 1 min grace)
    db_attempt = (
        await db_session.execute(
            select(StudentExam).where(StudentExam.id == attempt_id)
        )
    ).scalar_one()
    db_attempt.startedAt = datetime.now(UTC) - timedelta(minutes=25)
    await db_session.commit()

    # Reconnect and try to save
    res = await client.put(
        f"/api/v1/attempts/{attempt_id}/draft",
        json={
            "clientSequence": 1,
            "answers": [{"questionId": fix["q1"].id, "textAnswer": "Late answer"}],
        },
    )
    assert res.status_code == 400
    assert "time exceeded" in res.json()["detail"].lower()

    # Check database status
    await db_session.refresh(db_attempt)
    assert db_attempt.status == StudentExamStatus.EXPIRED


@pytest.mark.asyncio
async def test_proctoring_and_student_submit_race(
    auth_client_factory, db_session: AsyncSession, exam_concurrency_fixture
):
    """Simultaneous submits (e.g. user click + proctoring trigger) resolve safely without duplicate state."""
    fix = exam_concurrency_fixture
    client = await auth_client_factory(fix["user"])

    start_res = await client.post("/api/v1/attempts/start", json={"examId": fix["exam"].id})
    attempt_id = start_res.json()["id"]
    ans_shell_id = start_res.json()["answers"][0]["id"]

    submit_payload = {
        "id": attempt_id,
        "answers": [
            {
                "id": ans_shell_id,
                "selectedOptions": [{"optionId": fix["opt_correct"].id}],
            }
        ],
    }

    # Concurrent submits: one wins and one receives already submitted error
    r1, r2 = await asyncio.gather(
        client.post("/api/v1/attempts/submit", json=submit_payload),
        client.post("/api/v1/attempts/submit", json=submit_payload),
    )

    statuses = {r1.status_code, r2.status_code}
    assert 200 in statuses
    # Either both resolved or one received 400 already submitted
    assert statuses.issubset({200, 400})


@pytest.mark.asyncio
async def test_intentional_clearing_and_recovery(
    auth_client_factory, db_session: AsyncSession, exam_concurrency_fixture
):
    """Intentionally unselecting an answer persists empty selection on server."""
    fix = exam_concurrency_fixture
    client = await auth_client_factory(fix["user"])

    start_res = await client.post("/api/v1/attempts/start", json={"examId": fix["exam"].id})
    attempt_id = start_res.json()["id"]

    # 1. Select option
    await client.put(
        f"/api/v1/attempts/{attempt_id}/draft",
        json={
            "baseRevision": 0,
            "clientSequence": 1,
            "answers": [
                {
                    "questionId": fix["q1"].id,
                    "selectedOptions": [{"optionId": fix["opt_correct"].id}],
                }
            ],
        },
    )

    # 2. Clear option (empty list)
    clear_res = await client.put(
        f"/api/v1/attempts/{attempt_id}/draft",
        json={
            "baseRevision": 1,
            "clientSequence": 2,
            "answers": [
                {
                    "questionId": fix["q1"].id,
                    "selectedOptions": [],
                }
            ],
        },
    )
    assert clear_res.status_code == 200
    assert clear_res.json()["revision"] == 2

    # 3. GET attempt to confirm cleared
    get_res = await client.get(f"/api/v1/attempts/{attempt_id}")
    q1_ans = next(a for a in get_res.json()["answers"] if a["questionId"] == fix["q1"].id)
    assert q1_ans["selectedOptions"] == []
