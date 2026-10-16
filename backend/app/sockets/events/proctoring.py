"""Proctoring violation socket event constructors."""

from datetime import UTC, datetime, timezone
from typing import Any


def create_proctoring_warning_event(
    exam_id: str, student_id: str, warning_count: int, reason: str
) -> dict[str, Any]:
    """Constructs a proctoring warning event payload."""
    return {
        "event": "proctoring:warning",
        "data": {
            "examId": exam_id,
            "studentId": student_id,
            "warningCount": warning_count,
            "reason": reason,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    }


def create_proctoring_termination_event(
    exam_id: str, student_id: str, reason: str
) -> dict[str, Any]:
    """Constructs a proctoring auto-termination event payload."""
    return {
        "event": "proctoring:terminate",
        "data": {
            "examId": exam_id,
            "studentId": student_id,
            "reason": reason,
            "terminatedAt": datetime.now(UTC).isoformat(),
        },
    }
