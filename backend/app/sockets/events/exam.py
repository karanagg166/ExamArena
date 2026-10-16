"""Exam lifecycle socket event models and handlers."""

from datetime import UTC, datetime, timezone
from typing import Any


def create_exam_join_event(exam_id: str, user_id: str, role: str) -> dict[str, Any]:
    """Constructs an exam room join notification."""
    return {
        "event": "exam:join",
        "data": {
            "examId": exam_id,
            "userId": user_id,
            "role": role,
            "joinedAt": datetime.now(UTC).isoformat(),
        },
    }


def create_exam_submit_event(
    exam_id: str, student_id: str, attempt_id: str
) -> dict[str, Any]:
    """Constructs an exam submission broadcast notification."""
    return {
        "event": "exam:submit",
        "data": {
            "examId": exam_id,
            "studentId": student_id,
            "attemptId": attempt_id,
            "submittedAt": datetime.now(UTC).isoformat(),
        },
    }


def create_exam_time_sync_event(exam_id: str, remaining_seconds: int) -> dict[str, Any]:
    """Constructs a time synchronization event."""
    return {
        "event": "exam:time_sync",
        "data": {
            "examId": exam_id,
            "remainingSeconds": remaining_seconds,
            "syncedAt": datetime.now(UTC).isoformat(),
        },
    }
