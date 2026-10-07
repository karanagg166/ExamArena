"""Centralized deterministic identifier mapping for Search-Sphere.

This module owns all identity mapping between ExamArena entities and
Search-Sphere's multi-tenant identity hierarchy:

- Client Application ID: 'exam_arena'
- Tenant ID: 'school_<school_id>' (School is the organizational boundary)
- Collection ID: 'subject_<subject>' or 'class_<class_id>_subject_<subject>'
- Owner / Subject ID: 'user_<user_id>'
- External Document ID: '<material_id>'
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Union

from app.core.config import settings

if TYPE_CHECKING:
    from app.core.models import Subject


DEFAULT_CLIENT_ID = "exam_arena"
SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.:]+$")


def validate_identifier_token(val: str, field_name: str) -> str:
    """Validate that an ID string is non-empty and contains safe characters."""
    cleaned = str(val).strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty.")
    if not SAFE_ID_PATTERN.match(cleaned):
        raise ValueError(
            f"Invalid characters in {field_name} '{cleaned}'. "
            "Only alphanumeric, hyphens, dots, colons, and underscores allowed."
        )
    return cleaned


def build_client_id() -> str:
    """Return the stable Search-Sphere client application ID for ExamArena."""
    cid = (settings.SEARCH_SPHERE_CLIENT_ID or DEFAULT_CLIENT_ID).strip()
    return validate_identifier_token(cid, "client_id")


def build_tenant_id(school_id: str) -> str:
    """
    Derive the deterministic tenant ID from an ExamArena school ID.
    Example: 'school_sch_12345'
    """
    clean_school_id = validate_identifier_token(school_id, "school_id")
    return f"school_{clean_school_id}"


def parse_tenant_school_id(tenant_id: str) -> str:
    """Extract raw ExamArena school ID from Search-Sphere tenant ID."""
    clean = validate_identifier_token(tenant_id, "tenant_id")
    if clean.startswith("school_"):
        return clean[7:]
    return clean


def build_collection_id(
    subject: Union[Subject, str],
    class_id: str | None = None,
) -> str:
    """
    Derive the deterministic collection ID.
    If class_id is provided: 'class_<class_id>_subject_<subject>'
    Otherwise: 'subject_<subject>'

    Subject is normalized to lowercase string (e.g. 'science', 'maths').
    """
    raw_subject = subject.value if hasattr(subject, "value") else str(subject)
    clean_sub = validate_identifier_token(raw_subject.lower(), "subject")

    if class_id:
        clean_class = validate_identifier_token(class_id, "class_id")
        return f"class_{clean_class}_subject_{clean_sub}"
    return f"subject_{clean_sub}"


def build_owner_subject_id(user_id: str) -> str:
    """
    Derive owner/subject ID for documents uploaded to Search-Sphere.
    Example: 'user_usr_12345'
    """
    clean_user = validate_identifier_token(user_id, "user_id")
    return f"user_{clean_user}"


def build_external_document_id(material_id: str) -> str:
    """
    Derive external document ID from local ExamArena CourseMaterial ID.
    Must be stable, unique, and deterministic.
    """
    clean_mat = validate_identifier_token(material_id, "material_id")
    return clean_mat
