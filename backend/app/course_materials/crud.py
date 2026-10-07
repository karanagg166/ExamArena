"""Database CRUD operations for CourseMaterial."""

from __future__ import annotations

from typing import Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    CourseMaterial,
    CourseMaterialDocumentType,
    CourseMaterialStatus,
    Subject,
    generate_uuid,
    utc_now,
)


async def create_course_material(
    session: AsyncSession,
    school_id: str,
    subject: Subject,
    uploaded_by: str,
    title: str,
    original_file_name: str,
    file_size: int,
    mime_type: str,
    document_type: CourseMaterialDocumentType,
    search_sphere_collection_id: str,
    class_id: str | None = None,
    description: str | None = None,
    search_sphere_document_id: str | None = None,
    status: CourseMaterialStatus = CourseMaterialStatus.UPLOADED,
    processing_error: str | None = None,
) -> CourseMaterial:
    """Create and persist a new CourseMaterial row."""
    material = CourseMaterial(
        id=generate_uuid(),
        schoolId=school_id,
        subject=subject,
        classId=class_id,
        uploadedBy=uploaded_by,
        title=title,
        description=description,
        originalFileName=original_file_name,
        fileSize=file_size,
        mimeType=mime_type,
        documentType=document_type,
        searchSphereDocumentId=search_sphere_document_id,
        searchSphereCollectionId=search_sphere_collection_id,
        status=status,
        processingError=processing_error,
        createdAt=utc_now(),
        updatedAt=utc_now(),
    )
    session.add(material)
    await session.commit()
    await session.refresh(material)
    return material


async def get_course_material_by_id(
    session: AsyncSession,
    material_id: str,
) -> CourseMaterial | None:
    """Fetch CourseMaterial by primary ID."""
    stmt = select(CourseMaterial).where(CourseMaterial.id == material_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def list_course_materials(
    session: AsyncSession,
    school_id: str,
    subject: Subject | None = None,
    class_id: str | None = None,
    status: CourseMaterialStatus | None = None,
    document_type: CourseMaterialDocumentType | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[Sequence[CourseMaterial], int]:
    """List course materials scoped strictly to a school with pagination."""
    query = select(CourseMaterial).where(CourseMaterial.schoolId == school_id)

    if subject:
        query = query.where(CourseMaterial.subject == subject)
    if class_id:
        query = query.where(CourseMaterial.classId == class_id)
    if status:
        query = query.where(CourseMaterial.status == status)
    if document_type:
        query = query.where(CourseMaterial.documentType == document_type)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar_one() or 0

    paged_query = query.order_by(CourseMaterial.createdAt.desc()).limit(limit).offset(offset)
    items = (await session.execute(paged_query)).scalars().all()

    return items, total


async def update_course_material_status(
    session: AsyncSession,
    material_id: str,
    status: CourseMaterialStatus,
    search_sphere_document_id: str | None = None,
    processing_error: str | None = None,
) -> CourseMaterial | None:
    """Update material status, external document ID, or error message."""
    material = await get_course_material_by_id(session, material_id)
    if not material:
        return None

    material.status = status
    if search_sphere_document_id is not None:
        material.searchSphereDocumentId = search_sphere_document_id
    if processing_error is not None:
        material.processingError = processing_error
    material.updatedAt = utc_now()

    await session.commit()
    await session.refresh(material)
    return material


async def delete_course_material(
    session: AsyncSession,
    material_id: str,
) -> bool:
    """Delete a CourseMaterial record from ExamArena database."""
    material = await get_course_material_by_id(session, material_id)
    if not material:
        return False
    await session.delete(material)
    await session.commit()
    return True
