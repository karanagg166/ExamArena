import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock
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

    resp = await save_attempt_draft("att-1", update, "user-stu-1", session=mock_session)
    assert resp.savedCount == 1
    assert resp.clientSequence == 3
    assert mock_existing_answer.textAnswer == "New updated answer"
    mock_session.commit.assert_awaited_once()
    mock_set_seq.assert_awaited_once_with("att-1", 3)
