"""Validate Search Sphere states before synchronizing course material metadata."""

from app.core.models import CourseMaterialStatus
from app.integrations.search_sphere.exceptions import SearchSphereError


def processing_state(value: object) -> tuple[CourseMaterialStatus, str | None]:
    states = {
        "PENDING": CourseMaterialStatus.UPLOADED,
        "QUEUED": CourseMaterialStatus.UPLOADED,
        "PROCESSING": CourseMaterialStatus.PROCESSING,
        "READY": CourseMaterialStatus.READY,
        "FAILED": CourseMaterialStatus.FAILED,
    }
    if not isinstance(value, str) or value.strip().upper() not in states:
        raise SearchSphereError("Unsupported Search-Sphere processing state.")
    state = states[value.strip().upper()]
    error = (
        "Search-Sphere document processing failed. Retry ingestion."
        if state == CourseMaterialStatus.FAILED
        else None
    )
    return state, error
