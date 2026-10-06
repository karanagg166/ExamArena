"""Database CRUD operations for AnswerKeyImport entities."""

from datetime import datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

import app.core.database as db
from app.core.models import (
    AnswerKeyImport,
    AnswerKeyImportSourceType,
    AnswerKeyImportStatus,
    utc_now,
)


async def create_answer_key_import(
    exam_id: str,
    teacher_id: str,
    original_file_name: str,
    file_type: str,
    file_size: int,
    file_path: str,
    source_type: AnswerKeyImportSourceType = AnswerKeyImportSourceType.UNKNOWN,
    storage_provider: str | None = None,
    storage_key: str | None = None,
    storage_url: str | None = None,
    storage_resource_type: str | None = None,
    session: AsyncSession | None = None,
) -> AnswerKeyImport:
    """Creates a new AnswerKeyImport record with initial UPLOADED status."""
    import_obj = AnswerKeyImport(
        examId=exam_id,
        teacherId=teacher_id,
        originalFileName=original_file_name,
        fileType=file_type,
        fileSize=file_size,
        filePath=file_path,
        sourceType=source_type,
        status=AnswerKeyImportStatus.UPLOADED,
        storageProvider=storage_provider,
        storageKey=storage_key,
        storageUrl=storage_url,
        storageResourceType=storage_resource_type,
    )

    async def _do(s: AsyncSession):
        s.add(import_obj)
        await s.commit()
        await s.refresh(import_obj)
        return import_obj

    if session:
        return await _do(session)
    async with db.get_session() as s:
        return await _do(s)


async def get_answer_key_import_by_id(
    import_id: str, session: AsyncSession | None = None
) -> AnswerKeyImport | None:
    """Fetches an AnswerKeyImport record by its UUID."""

    async def _do(s: AsyncSession):
        stmt = select(AnswerKeyImport).where(AnswerKeyImport.id == import_id)
        res = await s.execute(stmt)
        return res.scalar_one_or_none()

    if session:
        return await _do(session)
    async with db.get_session() as s:
        return await _do(s)


async def list_answer_key_imports_by_exam_id(
    exam_id: str, session: AsyncSession | None = None
) -> list[AnswerKeyImport]:
    """Lists all answer key imports associated with a specific exam, newest first."""

    async def _do(s: AsyncSession):
        stmt = (
            select(AnswerKeyImport)
            .where(AnswerKeyImport.examId == exam_id)
            .order_by(desc(AnswerKeyImport.createdAt))
        )
        res = await s.execute(stmt)
        return list(res.scalars().all())

    if session:
        return await _do(session)
    async with db.get_session() as s:
        return await _do(s)


async def update_answer_key_import_processing_start(
    import_id: str, session: AsyncSession | None = None
) -> AnswerKeyImport | None:
    """Transition state to PROCESSING."""

    async def _do(s: AsyncSession):
        stmt = select(AnswerKeyImport).where(AnswerKeyImport.id == import_id)
        res = await s.execute(stmt)
        record = res.scalar_one_or_none()
        if record:
            record.status = AnswerKeyImportStatus.PROCESSING
            record.updatedAt = utc_now()
            await s.commit()
            await s.refresh(record)
        return record

    if session:
        return await _do(session)
    async with db.get_session() as s:
        return await _do(s)


async def update_answer_key_import_success(
    import_id: str,
    source_type: AnswerKeyImportSourceType,
    extracted_text: str | None,
    raw_extraction: dict[str, Any],
    validated_extraction: dict[str, Any],
    session: AsyncSession | None = None,
) -> AnswerKeyImport | None:
    """Transition state to NEEDS_REVIEW with extracted payload."""

    async def _do(s: AsyncSession):
        stmt = select(AnswerKeyImport).where(AnswerKeyImport.id == import_id)
        res = await s.execute(stmt)
        record = res.scalar_one_or_none()
        if record:
            record.status = AnswerKeyImportStatus.NEEDS_REVIEW
            record.sourceType = source_type
            record.extractedText = extracted_text
            record.rawExtraction = raw_extraction
            record.validatedExtraction = validated_extraction
            record.errorMessage = None
            record.errorCategory = None
            record.completedAt = utc_now()
            record.updatedAt = utc_now()
            await s.commit()
            await s.refresh(record)
        return record

    if session:
        return await _do(session)
    async with db.get_session() as s:
        return await _do(s)


async def update_answer_key_import_failure(
    import_id: str,
    error_category: str,
    error_message: str,
    session: AsyncSession | None = None,
) -> AnswerKeyImport | None:
    """Transition state to FAILED with descriptive error information."""

    async def _do(s: AsyncSession):
        stmt = select(AnswerKeyImport).where(AnswerKeyImport.id == import_id)
        res = await s.execute(stmt)
        record = res.scalar_one_or_none()
        if record:
            record.status = AnswerKeyImportStatus.FAILED
            record.errorCategory = error_category
            record.errorMessage = error_message
            record.completedAt = utc_now()
            record.updatedAt = utc_now()
            await s.commit()
            await s.refresh(record)
        return record

    if session:
        return await _do(session)
    async with db.get_session() as s:
        return await _do(s)


async def update_answer_key_import_draft(
    import_id: str,
    validated_extraction: dict[str, Any],
    session: AsyncSession | None = None,
) -> AnswerKeyImport | None:
    """Allows teacher to edit/refine the matched answers before final confirmation."""

    async def _do(s: AsyncSession):
        stmt = select(AnswerKeyImport).where(AnswerKeyImport.id == import_id)
        res = await s.execute(stmt)
        record = res.scalar_one_or_none()
        if record:
            record.validatedExtraction = validated_extraction
            record.updatedAt = utc_now()
            await s.commit()
            await s.refresh(record)
        return record

    if session:
        return await _do(session)
    async with db.get_session() as s:
        return await _do(s)


async def update_answer_key_import_confirmed(
    import_id: str,
    session: AsyncSession | None = None,
) -> AnswerKeyImport | None:
    """Transition state to COMPLETED upon confirmation."""

    async def _do(s: AsyncSession):
        stmt = select(AnswerKeyImport).where(AnswerKeyImport.id == import_id)
        res = await s.execute(stmt)
        record = res.scalar_one_or_none()
        if record:
            record.status = AnswerKeyImportStatus.COMPLETED
            record.confirmedAt = utc_now()
            record.updatedAt = utc_now()
            await s.commit()
            await s.refresh(record)
        return record

    if session:
        return await _do(session)
    async with db.get_session() as s:
        return await _do(s)
