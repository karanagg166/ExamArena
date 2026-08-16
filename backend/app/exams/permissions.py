from typing import Any

from app.core.models import Role
from app.exams.schemas import ExamResponse
from app.users.schemas import UserResponse


def can_manage_exam(
    current_user: UserResponse,
    teacher: Any | None,
    exam: ExamResponse,
) -> bool:
    """Return whether a user may view solutions or mutate an exam."""
    if current_user.role == Role.ADMIN:
        return True
    if not teacher or not exam.teacher:
        return False
    if exam.teacher.id == teacher.id:
        return True
    return bool(
        current_user.role == Role.PRINCIPAL
        and teacher.schoolId
        and exam.teacher.schoolId == teacher.schoolId
    )


def redact_exam_solutions(
    exam: Any,
    *,
    include_questions: bool,
    reveal_solutions: bool = False,
) -> ExamResponse:
    """Create a student-safe/public-safe exam payload without answer keys."""
    source = (
        exam if isinstance(exam, ExamResponse) else ExamResponse.model_validate(exam)
    )
    redacted = source.model_copy(deep=True)
    redacted.questionCount = len(redacted.questions or [])
    redacted.accessPassword = None

    if not include_questions:
        redacted.questions = []
        return redacted

    if not reveal_solutions:
        for question in redacted.questions or []:
            question.explanation = None
            for option in question.options or []:
                option.isCorrect = False
    return redacted
