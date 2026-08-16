import pytest
from pydantic import ValidationError

from app.questions.schemas import (
    QuestionBase,
    QuestionCreateRequest,
    QuestionOptionBase,
    QuestionType,
)


class TestQuestionValidation:
    def test_empty_question_text_raises_validation_error(self):
        """QuestionBase should reject empty or whitespace-only text."""
        with pytest.raises(ValidationError) as exc_info:
            QuestionBase(
                text="   ",
                marks=5,
                questionNumber=1,
                questionType=QuestionType.MULTIPLE_CHOICE,
                section="Section A",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("text",) for e in errors)
        assert any("Question text cannot be empty" in str(e["msg"]) for e in errors)

    def test_valid_question_text_passes(self):
        q = QuestionBase(
            text="What is the speed of light?",
            marks=5,
            questionNumber=1,
            questionType=QuestionType.MULTIPLE_CHOICE,
            section="Section A",
        )
        assert q.text == "What is the speed of light?"

    def test_rejects_non_positive_marks(self):
        with pytest.raises(ValidationError):
            QuestionBase(text="Invalid marks", marks=0)

    def test_rejects_multiple_correct_answers_for_single_choice(self):
        with pytest.raises(ValidationError, match="exactly one correct option"):
            QuestionCreateRequest(
                text="Choose one",
                questionType=QuestionType.MULTIPLE_CHOICE,
                options=[
                    {"text": "A", "optionNumber": 1, "isCorrect": True},
                    {"text": "B", "optionNumber": 2, "isCorrect": True},
                ],
            )


class TestOptionValidation:
    def test_empty_option_text_raises_validation_error(self):
        """QuestionOptionBase should reject empty or whitespace-only text."""
        with pytest.raises(ValidationError) as exc_info:
            QuestionOptionBase(text="   ", optionNumber=1)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("text",) for e in errors)
        assert any("Option text cannot be empty" in str(e["msg"]) for e in errors)

    def test_valid_option_text_passes(self):
        opt = QuestionOptionBase(text="299,792,458 m/s", optionNumber=1)
        assert opt.text == "299,792,458 m/s"
