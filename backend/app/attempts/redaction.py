"""Centralized redaction utilities for student exam attempts.

Protects sensitive grading data (scores, marks awarded, correctness flags, and feedback)
from exposure to students until the teacher explicitly releases the exam results.
"""

from app.attempts.schemas import StudentExamResponse


def redact_attempt_for_student(
    attempt: StudentExamResponse,
    *,
    is_results_released: bool,
) -> StudentExamResponse:
    """Redact sensitive grading information if results are not released.

    If results are not released:
    - marksObtained is set to None
    - answer marksAwarded is set to None
    - answer isCorrect is set to None
    - answer feedback is set to None
    - answer gradingStatus is set to None
    """
    if not isinstance(attempt, StudentExamResponse):
        attempt = StudentExamResponse.model_validate(attempt)

    if is_results_released:
        return attempt

    redacted = attempt.model_copy(deep=True)
    redacted.marksObtained = None

    if redacted.answers:
        for answer in redacted.answers:
            answer.marksAwarded = None
            answer.isCorrect = None
            answer.feedback = None
            answer.gradingStatus = None

    return redacted
