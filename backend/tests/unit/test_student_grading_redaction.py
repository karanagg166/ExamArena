"""Unit tests ensuring AI grading proposals and unreleased scores are never exposed to students."""

from datetime import datetime

from app.attempts.redaction import redact_attempt_for_student
from app.attempts.schemas import (
    AttemptStatus,
    Correctness,
    GradingStatus,
    QuestionType,
    StudentAnswerResponse,
    StudentExamResponse,
)


def test_student_answer_response_does_not_contain_ai_proposal_fields():
    """Verify StudentAnswerResponse schema never serializes internal AI proposal attributes."""
    schema = StudentAnswerResponse.model_json_schema()
    properties = schema.get("properties", {})

    # None of these internal AI grading fields should exist in student answer schema
    assert "aiSuggestedMarks" not in properties
    assert "aiConfidence" not in properties
    assert "aiFeedback" not in properties
    assert "aiGradingBreakdown" not in properties
    assert "aiWarnings" not in properties
    assert "aiGradedAt" not in properties
    assert "gradedBy" not in properties


def test_student_answer_model_validate_ignores_ai_attributes():
    """Verify that validating a dict/ORM object with AI fields does not leak them into student response."""
    data = {
        "id": "ans_1",
        "studentExamId": "attempt_1",
        "questionId": "q_1",
        "questionType": QuestionType.SHORT_ANSWER,
        "textAnswer": "Photosynthesis produces glucose and oxygen.",
        "marksAwarded": 4.5,
        "feedback": "Great explanation.",
        "isCorrect": Correctness.FULLY_CORRECT,
        "gradingStatus": GradingStatus.MANUALLY_GRADED,
        "aiSuggestedMarks": 4.5,
        "aiConfidence": "HIGH",
        "aiFeedback": "Internal AI note",
        "aiGradingBreakdown": [{"criterion": "Accurate", "marks": 5}],
        "aiWarnings": ["Internal warning"],
        "aiGradedAt": datetime.now(),
        "gradedBy": "teacher_user_id",
        "gradedAt": datetime.now(),
        "createdAt": datetime.now(),
        "updatedAt": datetime.now(),
        "selectedOptions": [],
    }

    resp = StudentAnswerResponse.model_validate(data)
    dumped = resp.model_dump()

    assert "aiSuggestedMarks" not in dumped
    assert "aiConfidence" not in dumped
    assert "aiFeedback" not in dumped
    assert "aiGradingBreakdown" not in dumped
    assert "aiWarnings" not in dumped
    assert "aiGradedAt" not in dumped
    assert "gradedBy" not in dumped
    assert dumped["marksAwarded"] == 4.5
    assert dumped["feedback"] == "Great explanation."


def test_redact_attempt_for_student_hides_all_grades_before_results_released():
    """Verify redact_attempt_for_student removes marks, correctness, feedback when unreleased."""
    answer = StudentAnswerResponse(
        id="ans_1",
        studentExamId="attempt_1",
        questionId="q_1",
        questionType=QuestionType.SHORT_ANSWER,
        textAnswer="My answer",
        marksAwarded=5.0,
        feedback="Teacher comments",
        isCorrect=Correctness.FULLY_CORRECT,
        gradingStatus=GradingStatus.MANUALLY_GRADED,
        createdAt=datetime.now(),
        updatedAt=datetime.now(),
        selectedOptions=[],
    )

    attempt = StudentExamResponse(
        id="attempt_1",
        studentId="student_1",
        examId="exam_1",
        marksObtained=25.0,
        status=AttemptStatus.GRADED,
        startedAt=datetime.now(),
        submittedAt=datetime.now(),
        createdAt=datetime.now(),
        updatedAt=datetime.now(),
        answers=[answer],
        isResultsReleased=False,
    )

    # When results are unreleased
    redacted = redact_attempt_for_student(attempt, is_results_released=False)
    assert redacted.marksObtained is None
    redacted_ans = redacted.answers[0]
    assert redacted_ans.marksAwarded is None
    assert redacted_ans.isCorrect is None
    assert redacted_ans.feedback is None
    assert redacted_ans.gradingStatus is None

    # When results are released
    revealed = redact_attempt_for_student(attempt, is_results_released=True)
    assert revealed.marksObtained == 25.0
    revealed_ans = revealed.answers[0]
    assert revealed_ans.marksAwarded == 5.0
    assert revealed_ans.feedback == "Teacher comments"
    assert revealed_ans.isCorrect == Correctness.FULLY_CORRECT
