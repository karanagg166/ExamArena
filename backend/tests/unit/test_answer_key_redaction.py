"""Unit tests for Answer Key and Rubric redaction in exam permissions."""

from datetime import datetime
from app.exams.permissions import redact_exam_solutions
from app.exams.schemas import ExamResponse, ExamType
from app.questions.schemas import QuestionOptionResponse, QuestionResponse, QuestionType


def test_redact_exam_solutions_strips_sensitive_data_before_release():
    fake_option1 = QuestionOptionResponse(
        id="opt_1", questionId="q_1", optionNumber=1, text="Wrong", isCorrect=False
    )
    fake_option2 = QuestionOptionResponse(
        id="opt_2", questionId="q_1", optionNumber=2, text="Right", isCorrect=True
    )
    fake_question = QuestionResponse(
        id="q_1",
        text="Sample question",
        marks=5,
        questionNumber=1,
        questionType=QuestionType.MULTIPLE_CHOICE,
        explanation="Secret explanation",
        referenceAnswer="Secret model answer",
        gradingRubric=[{"criterion": "Accuracy", "marks": 5}],
        createdAt=datetime.now(),
        updatedAt=datetime.now(),
        options=[fake_option1, fake_option2],
    )
    fake_exam = ExamResponse(
        id="exam_1",
        examCode="EXAM-1001",
        name="Security Exam",
        description="Security Exam Description",
        type=ExamType.MIDTERM,
        scheduledAt=datetime.now(),
        duration=60,
        maxMarks=100,
        createdAt=datetime.now(),
        updatedAt=datetime.now(),
        questions=[fake_question],
    )

    # 1. Unreleased results -> Solutions redacted
    redacted = redact_exam_solutions(fake_exam, include_questions=True, reveal_solutions=False)
    q = redacted.questions[0]
    assert q.explanation is None
    assert q.referenceAnswer is None
    assert q.gradingRubric is None
    for opt in q.options:
        assert opt.isCorrect is False

    # 2. Released results -> Solutions revealed
    revealed = redact_exam_solutions(fake_exam, include_questions=True, reveal_solutions=True)
    q_rev = revealed.questions[0]
    assert q_rev.explanation == "Secret explanation"
    assert q_rev.referenceAnswer == "Secret model answer"
    assert q_rev.gradingRubric == [{"criterion": "Accuracy", "marks": 5}]
    assert q_rev.options[1].isCorrect is True
