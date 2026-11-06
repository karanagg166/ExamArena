"""Recheck upstream source identities against the current local material catalog."""

from fastapi import HTTPException

from app.core.models import CourseMaterialStatus
from app.course_materials import crud


async def authorized_materials(session, items, school_id, subject, class_id, document_type=None):
    if not isinstance(items, list) or len(items) > 50 or any(
        not isinstance(item, dict) or not isinstance(item.get("document_id"), str) or not item["document_id"] for item in items
    ):
        raise HTTPException(502, "Search evidence could not be verified.")
    if not items:
        return {}
    identifiers = {item["document_id"] for item in items}
    rows = await crud.get_course_materials_by_ids(session, sorted(identifiers))
    approved = {}
    for row in rows:
        if row.schoolId != school_id or row.subject != subject or row.classId != class_id or row.status != CourseMaterialStatus.READY:
            continue
        if document_type is not None and row.documentType != document_type:
            continue
        approved[row.id] = row
        if row.searchSphereDocumentId:
            approved[row.searchSphereDocumentId] = row
    if not identifiers.issubset(approved):
        # Dropping citations alone would still disclose the answer they supported.
        raise HTTPException(502, "Search evidence could not be verified with current access.")
    return approved
