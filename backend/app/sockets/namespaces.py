"""Socket room and namespace identifier helpers."""


def exam_room(exam_id: str) -> str:
    """Format socket room name for an exam."""
    return f"exam:{exam_id.strip()}"


def user_room(user_id: str) -> str:
    """Format socket room name for a specific user."""
    return f"user:{user_id.strip()}"


def school_room(school_id: str) -> str:
    """Format socket room name for a school."""
    return f"school:{school_id.strip()}"


def proctoring_room(exam_id: str) -> str:
    """Format socket room name for proctoring an exam."""
    return f"proctoring:{exam_id.strip()}"


def chat_room(exam_id: str) -> str:
    """Format socket room name for exam chat."""
    return f"chat:{exam_id.strip()}"
