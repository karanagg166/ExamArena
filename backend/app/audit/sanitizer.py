from typing import Any

SENSITIVE_KEY_SUBSTRINGS = (
    "password",
    "pass",
    "token",
    "secret",
    "authorization",
    "auth",
    "cookie",
    "session",
    "jwt",
    "credential",
    "private",
    "api_key",
    "apikey",
    "hash",
    "ssn",
    "credit_card",
    "cvv",
)

REDACTED_VALUE = "[REDACTED]"
MAX_STRING_LENGTH = 1000
MAX_DEPTH = 5


def is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(sub in normalized for sub in SENSITIVE_KEY_SUBSTRINGS)


def sanitize_metadata(data: Any, depth: int = 0) -> Any:
    """Recursively scrub sensitive keys and limit depth/string lengths for audit log metadata."""
    if depth > MAX_DEPTH:
        return "[TRUNCATED_DEPTH]"

    if data is None:
        return None

    if isinstance(data, (bool, int, float)):
        return data

    if isinstance(data, str):
        if len(data) > MAX_STRING_LENGTH:
            return data[:MAX_STRING_LENGTH] + "... [TRUNCATED]"
        return data

    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for key, value in data.items():
            str_key = str(key)
            if is_sensitive_key(str_key):
                cleaned[str_key] = REDACTED_VALUE
            else:
                cleaned[str_key] = sanitize_metadata(value, depth=depth + 1)
        return cleaned

    if isinstance(data, (list, tuple, set)):
        return [sanitize_metadata(item, depth=depth + 1) for item in list(data)[:50]]

    # For objects or Pydantic models with model_dump or __dict__
    if hasattr(data, "model_dump") and callable(data.model_dump):
        return sanitize_metadata(data.model_dump(), depth=depth + 1)
    if hasattr(data, "__dict__"):
        return sanitize_metadata(vars(data), depth=depth + 1)

    return str(data)[:MAX_STRING_LENGTH]
