# backend/tests/attempts/test_msq_grading.py
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.attempts import crud as attempts_crud
from app.attempts.schemas import (
    SelectedOptionCreate,
    StudentAnswerUpdate,
    StudentExamSubmit,
)
from app.core.models import Correctness, GradingStatus, QuestionType


def _make_mock_attempt(attempt_id: str, ans_mock: MagicMock, exam_mock: MagicMock):
    att = MagicMock()
    att.id = attempt_id
    att.studentId = "student_1"
    att.examId = "clxfake_exam_001"
    att.status = "IN_PROGRESS"
    att.marksObtained = 0.0
    att.startedAt = datetime(2026, 1, 1)
    att.submittedAt = None
    att.createdAt = datetime(2026, 1, 1)
    att.updatedAt = datetime(2026, 1, 1)
    att.answers = [ans_mock]
    att.exam = exam_mock
    return att


def _make_mock_answer(ans_id: str, question_id: str):
    ans = MagicMock()
    ans.id = ans_id
    ans.studentExamId = "att_1"
    ans.questionId = question_id
    ans.questionType = QuestionType.MULTIPLE_SELECT
    ans.marksAwarded = 0.0
    ans.feedback = None
    ans.isCorrect = Correctness.INCORRECT
    ans.gradingStatus = GradingStatus.PENDING
    ans.selectedOptions = []
    ans.textAnswer = None
    ans.createdAt = datetime(2026, 1, 1)
    ans.updatedAt = datetime(2026, 1, 1)
    return ans


@pytest.mark.asyncio
class TestMsqAndNegativeGrading:
    async def test_msq_full_marks_when_all_correct_and_zero_wrong(self):
        """When student selects all correct options and no wrong options -> Full Marks"""
        q_mock = MagicMock()
        q_mock.id = "q_msq_1"
        q_mock.questionType = QuestionType.MULTIPLE_SELECT
        q_mock.marks = 4.0
        q_mock.negativeMarks = 1.0

        opt1 = MagicMock(id="opt_1", isCorrect=True)
        opt2 = MagicMock(id="opt_2", isCorrect=True)
        opt3 = MagicMock(id="opt_3", isCorrect=False)
        opt4 = MagicMock(id="opt_4", isCorrect=False)
        q_mock.options = [opt1, opt2, opt3, opt4]

        ans_mock = _make_mock_answer("ans_1", "q_msq_1")

        exam_mock = MagicMock()
        exam_mock.negativeMarking = True
        exam_mock.negativeMarks = 1.0
        exam_mock.questions = [q_mock]
        exam_mock.isResultsReleased = False

        attempt_mock = _make_mock_attempt("att_1", ans_mock, exam_mock)

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = attempt_mock
        mock_result.scalar_one.return_value = attempt_mock
        mock_session.execute.return_value = mock_result

        with (
            patch(
                "app.attempts.crud.get_student_by_user_id",
                new=AsyncMock(return_value=MagicMock(id="student_1")),
            ),
            patch(
                "app.attempts.crud.get_attempt_by_id",
                new=AsyncMock(return_value=attempt_mock),
            ),
        ):
            submit_data = StudentExamSubmit(
                id="att_1",
                answers=[
                    StudentAnswerUpdate(
                        id="ans_1",
                        selectedOptions=[
                            SelectedOptionCreate(optionId="opt_1"),
                            SelectedOptionCreate(optionId="opt_2"),
                        ],
                    )
                ],
            )
            resp = await attempts_crud.submit_exam_attempt(
                submit_data, "user_1", session=mock_session
            )

            assert ans_mock.marksAwarded == 4.0
            assert ans_mock.isCorrect == Correctness.FULLY_CORRECT
            assert ans_mock.gradingStatus == GradingStatus.AUTO_GRADED
            assert resp.marksObtained == 4.0

    async def test_msq_partial_marks_when_subset_of_correct_and_zero_wrong(self):
        """When student selects 1 of 2 correct options and no wrong options -> 2.0 / 4.0 Marks"""
        q_mock = MagicMock()
        q_mock.id = "q_msq_2"
        q_mock.questionType = QuestionType.MULTIPLE_SELECT
        q_mock.marks = 4.0
        q_mock.negativeMarks = 1.0

        opt1 = MagicMock(id="opt_1", isCorrect=True)
        opt2 = MagicMock(id="opt_2", isCorrect=True)
        opt3 = MagicMock(id="opt_3", isCorrect=False)
        q_mock.options = [opt1, opt2, opt3]

        ans_mock = _make_mock_answer("ans_2", "q_msq_2")

        exam_mock = MagicMock()
        exam_mock.negativeMarking = True
        exam_mock.negativeMarks = 1.0
        exam_mock.questions = [q_mock]
        exam_mock.isResultsReleased = False

        attempt_mock = _make_mock_attempt("att_2", ans_mock, exam_mock)

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = attempt_mock
        mock_result.scalar_one.return_value = attempt_mock
        mock_session.execute.return_value = mock_result

        with (
            patch(
                "app.attempts.crud.get_student_by_user_id",
                new=AsyncMock(return_value=MagicMock(id="student_1")),
            ),
            patch(
                "app.attempts.crud.get_attempt_by_id",
                new=AsyncMock(return_value=attempt_mock),
            ),
        ):
            submit_data = StudentExamSubmit(
                id="att_2",
                answers=[
                    StudentAnswerUpdate(
                        id="ans_2",
                        selectedOptions=[SelectedOptionCreate(optionId="opt_1")],
                    )
                ],
            )
            resp = await attempts_crud.submit_exam_attempt(
                submit_data, "user_1", session=mock_session
            )

            assert ans_mock.marksAwarded == 2.0  # (1/2) * 4.0
            assert ans_mock.isCorrect == Correctness.PARTIALLY_CORRECT
            assert ans_mock.gradingStatus == GradingStatus.AUTO_GRADED
            assert resp.marksObtained == 2.0

    async def test_msq_negative_marks_when_wrong_option_selected(self):
        """When student selects a wrong option -> -1.0 deduction"""
        q_mock = MagicMock()
        q_mock.id = "q_msq_3"
        q_mock.questionType = QuestionType.MULTIPLE_SELECT
        q_mock.marks = 4.0
        q_mock.negativeMarks = 1.0

        opt1 = MagicMock(id="opt_1", isCorrect=True)
        opt2 = MagicMock(id="opt_2", isCorrect=True)
        opt3 = MagicMock(id="opt_3", isCorrect=False)
        q_mock.options = [opt1, opt2, opt3]

        ans_mock = _make_mock_answer("ans_3", "q_msq_3")

        exam_mock = MagicMock()
        exam_mock.negativeMarking = True
        exam_mock.negativeMarks = 1.0
        exam_mock.questions = [q_mock]
        exam_mock.isResultsReleased = False

        attempt_mock = _make_mock_attempt("att_3", ans_mock, exam_mock)

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = attempt_mock
        mock_result.scalar_one.return_value = attempt_mock
        mock_session.execute.return_value = mock_result

        with (
            patch(
                "app.attempts.crud.get_student_by_user_id",
                new=AsyncMock(return_value=MagicMock(id="student_1")),
            ),
            patch(
                "app.attempts.crud.get_attempt_by_id",
                new=AsyncMock(return_value=attempt_mock),
            ),
        ):
            submit_data = StudentExamSubmit(
                id="att_3",
                answers=[
                    StudentAnswerUpdate(
                        id="ans_3",
                        selectedOptions=[
                            SelectedOptionCreate(optionId="opt_1"),
                            SelectedOptionCreate(optionId="opt_3"),
                        ],
                    )
                ],
            )
            resp = await attempts_crud.submit_exam_attempt(
                submit_data, "user_1", session=mock_session
            )

            assert ans_mock.marksAwarded == -1.0
            assert ans_mock.isCorrect == Correctness.INCORRECT
            assert ans_mock.gradingStatus == GradingStatus.AUTO_GRADED
            assert resp.marksObtained == 0.0  # max(0, -1.0) for overall exam
