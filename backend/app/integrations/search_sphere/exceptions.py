"""Exception definitions and error boundaries for Search-Sphere integration.

Guarantees:
- Safe client-facing error summaries
- Upstream internal error details are never exposed directly to users
- API keys, credentials, and sensitive tokens are strictly redacted
"""

from __future__ import annotations

import re
from typing import Any


def sanitize_sensitive_message(msg: str) -> str:
    """Scrub potential API keys, bearer tokens, or secrets from exception text."""
    if not msg:
        return ""
    # Redact Bearer tokens
    sanitized = re.sub(r"Bearer\s+[a-zA-Z0-9_\-\.]+", "Bearer [REDACTED]", msg)
    # Redact ss_live_ or ss_test_ keys
    sanitized = re.sub(r"ss_[a-zA-Z0-9_\-]+", "[REDACTED_API_KEY]", sanitized)
    # Redact generic key patterns
    sanitized = re.sub(r"([a-zA-Z0-9_\-]{32,})", "[REDACTED_TOKEN]", sanitized)
    return sanitized


class SearchSphereError(Exception):
    """Base exception for Search-Sphere microservice errors."""

    def __init__(self, message: str, status_code: int | None = None, details: Any = None):
        clean_msg = sanitize_sensitive_message(message)
        super().__init__(clean_msg)
        self.message = clean_msg
        self.status_code = status_code
        self.details = details

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, status_code={self.status_code})"


class SearchSphereConfigurationError(SearchSphereError):
    """Raised when integration settings or credentials are misconfigured."""
    pass


class SearchSphereAuthenticationError(SearchSphereError):
    """Raised when authentication with Search-Sphere fails (401)."""
    pass


class SearchSphereAuthorizationError(SearchSphereError):
    """Raised when client lacks permission or tenant access is forbidden (403)."""
    pass


class SearchSphereNotFoundError(SearchSphereError):
    """Raised when requested Search-Sphere collection or document is not found (404)."""
    pass


class SearchSphereConflictError(SearchSphereError):
    """Raised when duplicate resource exists in Search-Sphere (409)."""
    pass


class SearchSphereValidationError(SearchSphereError):
    """Raised when request payload or parameters fail validation (400 / 422)."""
    pass


class SearchSphereTimeoutError(SearchSphereError):
    """Raised when HTTP request to Search-Sphere times out."""
    pass


class SearchSphereUnavailableError(SearchSphereError):
    """Raised when Search-Sphere service is unavailable or returns 5xx."""
    pass
