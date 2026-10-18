from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.attempts.crud import save_attempt_draft
from app.attempts.schemas import StudentDraftAnswerItem, StudentExamDraftUpdate
from app.core.models import (
    Exam,
    Question,
    QuestionOption,
    QuestionType,
    Role,
    Student,
    StudentExam,
    StudentExamAnswer,
    StudentExamStatus,
)


@pytest.mark.asyncio
async def test_save_draft_rejects_non_student(mocker):
    mocker.patch("app.attempts.crud.get_student_by_user_id", return_value=None)
    update = StudentExamDraftUpdate(clientSequence=1, answers=[])
    with pytest.raises(ValueError, match="Only students can save drafts"):
        await save_attempt_draft("att-1", update, "user-teacher")


@pytest.mark.asyncio
async def test_save_draft_rejects_cross_student(mocker):
    mock_student = MagicMock(spec=Student)
    mock_student.id = "stu-1"
    mocker.patch("app.attempts.crud.get_student_by_user_id", return_value=mock_student)

    # Attempt belongs to stu-2
    mock_attempt = MagicMock(spec=StudentExam)
    mock_attempt.studentId = "stu-2"
    mock_attempt.status = StudentExamStatus.IN_PROGRESS

    mock_session = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_attempt
    mock_session.execute.return_value = mock_res

    update = StudentExamDraftUpdate(clientSequence=1, answers=[])
    with pytest.raises(ValueError, match="Not authorized to modify this attempt"):
        await save_attempt_draft("att-1", update, "user-stu-1", session=mock_session)


@pytest.mark.asyncio
async def test_save_draft_rejects_submitted_or_expired(mocker):
    mock_student = MagicMock(spec=Student)
    mock_student.id = "stu-1"
    mocker.patch("app.attempts.crud.get_student_by_user_id", return_value=mock_student)

    mock_attempt = MagicMock(spec=StudentExam)
    mock_attempt.studentId = "stu-1"
    mock_attempt.status = StudentExamStatus.SUBMITTED

    mock_session = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_attempt
    mock_session.execute.return_value = mock_res

    update = StudentExamDraftUpdate(clientSequence=1, answers=[])
    with pytest.raises(ValueError, match="Cannot modify answers for an already submitted attempt"):
        await save_attempt_draft("att-1", update, "user-stu-1", session=mock_session)


@pytest.mark.asyncio
async def test_save_draft_rejects_expired_deadline(mocker):
    mock_student = MagicMock(spec=Student)
    mock_student.id = "stu-1"
    mocker.patch("app.attempts.crud.get_student_by_user_id", return_value=mock_student)

    mock_exam = MagicMock(spec=Exam)
    mock_exam.duration = 60  # 60 minutes

    mock_attempt = MagicMock(spec=StudentExam)
    mock_attempt.studentId = "stu-1"
    mock_attempt.status = StudentExamStatus.IN_PROGRESS
    mock_attempt.startedAt = datetime.now(UTC) - timedelta(minutes=70)  # past 60 + 1 min grace
    mock_attempt.exam = mock_exam

    mock_session = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_attempt
    mock_session.execute.return_value = mock_res

    update = StudentExamDraftUpdate(clientSequence=1, answers=[])
    with pytest.raises(ValueError, match="Exam submission time exceeded"):
        await save_attempt_draft("att-1", update, "user-stu-1", session=mock_session)

    assert mock_attempt.status == StudentExamStatus.EXPIRED


@pytest.mark.asyncio
async def test_save_draft_out_of_order_sequence_ignored(mocker):
    mock_student = MagicMock(spec=Student)
    mock_student.id = "stu-1"
    mocker.patch("app.attempts.crud.get_student_by_user_id", return_value=mock_student)
    mocker.patch("app.attempts.crud._get_draft_sequence", return_value=5)

    mock_exam = MagicMock(spec=Exam)
    mock_exam.duration = 60

    mock_attempt = MagicMock(spec=StudentExam)
    mock_attempt.id = "att-1"
    mock_attempt.studentId = "stu-1"
    mock_attempt.status = StudentExamStatus.IN_PROGRESS
    mock_attempt.startedAt = datetime.now(UTC) - timedelta(minutes=10)
    mock_attempt.exam = mock_exam

    mock_session = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_attempt
    mock_session.execute.return_value = mock_res

    # Client sends stale sequence 3 when server already has sequence 5
    update = StudentExamDraftUpdate(clientSequence=3, answers=[])
    resp = await save_attempt_draft("att-1", update, "user-stu-1", session=mock_session)
    assert resp.savedCount == 0
    assert resp.clientSequence == 3
    # Commit must NOT be called for stale updates
    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_save_draft_success_flow(mocker):
    mock_student = MagicMock(spec=Student)
    mock_student.id = "stu-1"
    mocker.patch("app.attempts.crud.get_student_by_user_id", return_value=mock_student)
    mocker.patch("app.attempts.crud._get_draft_sequence", return_value=2)
    mock_set_seq = mocker.patch("app.attempts.crud._set_draft_sequence", new_callable=AsyncMock)

    mock_opt1 = MagicMock(spec=QuestionOption)
    mock_opt1.id = "opt-1"
    mock_opt2 = MagicMock(spec=QuestionOption)
    mock_opt2.id = "opt-2"

    mock_question = MagicMock(spec=Question)
    mock_question.id = "q-1"
    mock_question.type = QuestionType.MULTIPLE_CHOICE
    mock_question.options = [mock_opt1, mock_opt2]

    mock_exam = MagicMock(spec=Exam)
    mock_exam.duration = 60
    mock_exam.questions = [mock_question]

    mock_existing_answer = MagicMock(spec=StudentExamAnswer)
    mock_existing_answer.id = "ans-1"
    mock_existing_answer.questionId = "q-1"
    mock_existing_answer.textAnswer = "Old answer"
    mock_existing_answer.selectedOptions = []

    mock_attempt = MagicMock(spec=StudentExam)
    mock_attempt.id = "att-1"
    mock_attempt.studentId = "stu-1"
    mock_attempt.status = StudentExamStatus.IN_PROGRESS
    mock_attempt.startedAt = datetime.now(UTC) - timedelta(minutes=10)
    mock_attempt.exam = mock_exam
    mock_attempt.answers = [mock_existing_answer]

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_attempt
    mock_session.execute.return_value = mock_res

    from app.attempts.schemas import SelectedOptionCreate
    update = StudentExamDraftUpdate(
        clientSequence=3,
        answers=[
            StudentDraftAnswerItem(
                id="ans-1",
                questionId="q-1",
                textAnswer="New updated answer",
                selectedOptions=[SelectedOptionCreate(optionId="opt-2")],
            )
        ],
    )

    mock_attempt.draftRevision = 2

    resp = await save_attempt_draft("att-1", update, "user-stu-1", session=mock_session)
    assert resp.savedCount == 1
    assert resp.clientSequence == 3
    assert resp.applied is True
    assert resp.conflict is False
    assert resp.revision == 3
    assert mock_attempt.draftRevision == 3
    assert mock_existing_answer.textAnswer == "New updated answer"
    mock_session.commit.assert_awaited_once()
    mock_set_seq.assert_awaited_once_with("att-1", 3)


@pytest.mark.asyncio
async def test_save_draft_durable_base_revision_concurrency(mocker):
    """Saving with a matching baseRevision succeeds and increments draftRevision."""
    mock_student = MagicMock(spec=Student)
    mock_student.id = "stu-1"
    mocker.patch("app.attempts.crud.get_student_by_user_id", return_value=mock_student)

    mock_question = MagicMock(spec=Question)
    mock_question.id = "q-1"
    mock_question.type = QuestionType.SHORT_ANSWER
    mock_question.options = []

    mock_exam = MagicMock(spec=Exam)
    mock_exam.duration = 60
    mock_exam.questions = [mock_question]

    mock_attempt = MagicMock(spec=StudentExam)
    mock_attempt.id = "att-1"
    mock_attempt.studentId = "stu-1"
    mock_attempt.status = StudentExamStatus.IN_PROGRESS
    mock_attempt.startedAt = datetime.now(UTC) - timedelta(minutes=5)
    mock_attempt.draftRevision = 4  # Server is at revision 4
    mock_attempt.exam = mock_exam
    mock_attempt.answers = []

    mock_session = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_attempt
    mock_session.execute.return_value = mock_res

    # Tab A sends baseRevision=4
    update = StudentExamDraftUpdate(
        baseRevision=4,
        clientSequence=10,
        answers=[StudentDraftAnswerItem(questionId="q-1", textAnswer="Photosynthesis")],
    )
    resp = await save_attempt_draft("att-1", update, "user-stu-1", session=mock_session)
    assert resp.applied is True
    assert resp.conflict is False
    assert resp.revision == 5
    assert mock_attempt.draftRevision == 5
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_draft_stale_tab_conflict_rejected(mocker):
    """A stale tab sending an older baseRevision is rejected with conflict=True and not applied."""
    mock_student = MagicMock(spec=Student)
    mock_student.id = "stu-1"
    mocker.patch("app.attempts.crud.get_student_by_user_id", return_value=mock_student)

    mock_question = MagicMock(spec=Question)
    mock_question.id = "q-1"
    mock_question.type = QuestionType.SHORT_ANSWER
    mock_question.options = []

    mock_exam = MagicMock(spec=Exam)
    mock_exam.duration = 60
    mock_exam.questions = [mock_question]

    mock_attempt = MagicMock(spec=StudentExam)
    mock_attempt.id = "att-1"
    mock_attempt.studentId = "stu-1"
    mock_attempt.status = StudentExamStatus.IN_PROGRESS
    mock_attempt.startedAt = datetime.now(UTC) - timedelta(minutes=5)
    mock_attempt.draftRevision = 7  # Server has advanced to revision 7
    mock_attempt.exam = mock_exam
    mock_attempt.answers = []

    mock_session = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_attempt
    mock_session.execute.return_value = mock_res

    # Stale second tab sends baseRevision=5
    update = StudentExamDraftUpdate(
        baseRevision=5,
        clientSequence=3,
        answers=[StudentDraftAnswerItem(questionId="q-1", textAnswer="Stale text from old tab")],
    )
    resp = await save_attempt_draft("att-1", update, "user-stu-1", session=mock_session)
    assert resp.applied is False
    assert resp.conflict is True
    assert resp.savedCount == 0
    assert resp.revision == 7  # Reports current server revision
    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_save_draft_rejects_mismatched_answer_and_question_id(mocker):
    """Supplying an answer ID belonging to question A with questionId set to question B is rejected."""
    mock_student = MagicMock(spec=Student)
    mock_student.id = "stu-1"
    mocker.patch("app.attempts.crud.get_student_by_user_id", return_value=mock_student)

    mock_q1 = MagicMock(spec=Question)
    mock_q1.id = "q-1"
    mock_q1.type = QuestionType.SHORT_ANSWER
    mock_q1.options = []

    mock_q2 = MagicMock(spec=Question)
    mock_q2.id = "q-2"
    mock_q2.type = QuestionType.SHORT_ANSWER
    mock_q2.options = []

    mock_exam = MagicMock(spec=Exam)
    mock_exam.duration = 60
    mock_exam.questions = [mock_q1, mock_q2]

    # ans-1 belongs to q-1
    mock_ans1 = MagicMock(spec=StudentExamAnswer)
    mock_ans1.id = "ans-1"
    mock_ans1.questionId = "q-1"
    mock_ans1.textAnswer = "Q1 answer"

    mock_attempt = MagicMock(spec=StudentExam)
    mock_attempt.id = "att-1"
    mock_attempt.studentId = "stu-1"
    mock_attempt.status = StudentExamStatus.IN_PROGRESS
    mock_attempt.startedAt = datetime.now(UTC) - timedelta(minutes=5)
    mock_attempt.draftRevision = 1
    mock_attempt.exam = mock_exam
    mock_attempt.answers = [mock_ans1]

    mock_session = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_attempt
    mock_session.execute.return_value = mock_res

    # Client tries to send ans-1 with questionId="q-2"
    update = StudentExamDraftUpdate(
        baseRevision=1,
        answers=[StudentDraftAnswerItem(id="ans-1", questionId="q-2", textAnswer="Hacked")],
    )
    with pytest.raises(ValueError, match="Answer ID ans-1 belongs to question q-1, not q-2"):
        await save_attempt_draft("att-1", update, "user-stu-1", session=mock_session)


@pytest.mark.asyncio
async def test_save_draft_rejects_foreign_options(mocker):
    """Selecting options that belong to a different question is rejected."""
    mock_student = MagicMock(spec=Student)
    mock_student.id = "stu-1"
    mocker.patch("app.attempts.crud.get_student_by_user_id", return_value=mock_student)

    mock_opt1 = MagicMock(spec=QuestionOption)
    mock_opt1.id = "opt-valid-1"

    mock_q1 = MagicMock(spec=Question)
    mock_q1.id = "q-1"
    mock_q1.type = QuestionType.MULTIPLE_CHOICE
    mock_q1.options = [mock_opt1]

    mock_exam = MagicMock(spec=Exam)
    mock_exam.duration = 60
    mock_exam.questions = [mock_q1]

    mock_attempt = MagicMock(spec=StudentExam)
    mock_attempt.id = "att-1"
    mock_attempt.studentId = "stu-1"
    mock_attempt.status = StudentExamStatus.IN_PROGRESS
    mock_attempt.startedAt = datetime.now(UTC) - timedelta(minutes=5)
    mock_attempt.draftRevision = 0
    mock_attempt.exam = mock_exam
    mock_attempt.answers = []

    mock_session = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_attempt
    mock_session.execute.return_value = mock_res

    from app.attempts.schemas import SelectedOptionCreate
    update = StudentExamDraftUpdate(
        baseRevision=0,
        answers=[
            StudentDraftAnswerItem(
                questionId="q-1",
                selectedOptions=[SelectedOptionCreate(optionId="opt-foreign-999")],
            )
        ],
    )
    with pytest.raises(ValueError, match="Invalid option selection for question q-1"):
        await save_attempt_draft("att-1", update, "user-stu-1", session=mock_session)

