import pytest

from app.audit.context import (
    clear_audit_context,
    get_current_actor,
    get_current_client_ip,
    get_current_request_id,
    get_current_user_agent,
    set_current_actor,
    set_current_client_ip,
    set_current_request_id,
    set_current_user_agent,
)
from app.audit.sanitizer import sanitize_metadata


def test_sanitize_metadata_redacts_sensitive_keys():
    raw = {
        "email": "user@example.com",
        "password": "supersecretpassword",
        "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "auth_header": "Bearer 12345",
        "cookie": "session=abcde",
        "nested": {
            "api_key": "secret-api-key",
            "safe_field": "visible_value",
            "private_token": "sensitive",
        },
        "list_items": [
            {"password_hash": "hash123", "id": "1"},
            {"name": "test"},
        ],
    }

    sanitized = sanitize_metadata(raw)
    assert sanitized["email"] == "user@example.com"
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["accessToken"] == "[REDACTED]"
    assert sanitized["auth_header"] == "[REDACTED]"
    assert sanitized["cookie"] == "[REDACTED]"
    assert sanitized["nested"]["api_key"] == "[REDACTED]"
    assert sanitized["nested"]["safe_field"] == "visible_value"
    assert sanitized["nested"]["private_token"] == "[REDACTED]"
    assert sanitized["list_items"][0]["password_hash"] == "[REDACTED]"
    assert sanitized["list_items"][0]["id"] == "1"
    assert sanitized["list_items"][1]["name"] == "test"


def test_sanitize_metadata_handles_non_dict_and_none():
    assert sanitize_metadata(None) is None
    assert sanitize_metadata("not a dict") == "not a dict"
    assert sanitize_metadata(123) == 123


def test_sanitize_metadata_truncates_long_strings():
    raw = {"large_text": "x" * 2000}
    sanitized = sanitize_metadata(raw)
    assert len(sanitized["large_text"]) == 1000 + len("... [TRUNCATED]")
    assert sanitized["large_text"].endswith("... [TRUNCATED]")


def test_audit_contextvars():
    clear_audit_context()
    assert get_current_request_id() is None
    assert get_current_client_ip() is None
    assert get_current_user_agent() is None
    assert get_current_actor() is None

    set_current_request_id("req-12345")
    set_current_client_ip("192.168.1.100")
    set_current_user_agent("Mozilla/5.0 TestBrowser")
    set_current_actor("user-1", "user1@example.com", "TEACHER")

    assert get_current_request_id() == "req-12345"
    assert get_current_client_ip() == "192.168.1.100"
    assert get_current_user_agent() == "Mozilla/5.0 TestBrowser"
    assert get_current_actor() == {
        "id": "user-1",
        "email": "user1@example.com",
        "role": "TEACHER",
    }

    clear_audit_context()
    assert get_current_request_id() is None
    assert get_current_actor() is None
