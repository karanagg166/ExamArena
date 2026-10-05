"""Database CRUD operations for QuestionImport entities."""

from datetime import datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

import app.core.database as db
from app.core.models import (
    QuestionImport,
    QuestionImportSourceType,
    QuestionImportStatus,
    utc_now,
)


async def create_question_import(
    exam_id: str,
    teacher_id: str,
    original_file_name: str,
    file_type: str,
    file_size: int,
    file_path: str,
    source_type: QuestionImportSourceType = QuestionImportSourceType.UNKNOWN,
    session: AsyncSession | None = None,
) -> QuestionImport:
    """Creates a new QuestionImport record with initial UPLOADED status."""
    import_obj = QuestionImport(
        examId=exam_id,
        teacherId=teacher_id,
        originalFileName=original_file_name,
        fileType=file_type,
        fileSize=file_size,
        filePath=file_path,
        sourceType=source_type,
        status=QuestionImportStatus.UPLOADED,
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


async def get_question_import_by_id(
    import_id: str, session: AsyncSession | None = None
) -> QuestionImport | None:
    """Fetches a QuestionImport record by its UUID."""

    async def _do(s: AsyncSession):
        stmt = select(QuestionImport).where(QuestionImport.id == import_id)
        res = await s.execute(stmt)
        return res.scalar_one_or_none()

    if session:
        return await _do(session)
    async with db.get_session() as s:
        return await _do(s)


async def list_question_imports_by_exam_id(
    exam_id: str, session: AsyncSession | None = None
) -> list[QuestionImport]:
    """Lists all imports associated with a specific exam, newest first."""

    async def _do(s: AsyncSession):
        stmt = (
            select(QuestionImport)
            .where(QuestionImport.examId == exam_id)
            .order_by(desc(QuestionImport.createdAt))
        )
        res = await s.execute(stmt)
        return list(res.scalars().all())

    if session:
        return await _do(session)
    async with db.get_session() as s:
        return await _do(s)


async def update_question_import_processing_start(
    import_id: str, session: AsyncSession | None = None
) -> QuestionImport | None:
    """Transition state to PROCESSING."""

    async def _do(s: AsyncSession):
        stmt = select(QuestionImport).where(QuestionImport.id == import_id)
        res = await s.execute(stmt)
        record = res.scalar_one_or_none()
        if record:
            record.status = QuestionImportStatus.PROCESSING
            record.updatedAt = utc_now()
            await s.commit()
            await s.refresh(record)
        return record

    if session:
        return await _do(session)
    async with db.get_session() as s:
        return await _do(s)


async def update_question_import_success(
    import_id: str,
    source_type: QuestionImportSourceType,
    extracted_text: str,
    raw_extraction: dict[str, Any] | list[Any],
    validated_extraction: dict[str, Any],
    session: AsyncSession | None = None,
) -> QuestionImport | None:
    """Persists successful extraction draft and transitions state to NEEDS_REVIEW."""

    async def _do(s: AsyncSession):
        stmt = select(QuestionImport).where(QuestionImport.id == import_id)
        res = await s.execute(stmt)
        record = res.scalar_one_or_none()
        if record:
            record.sourceType = source_type
            record.extractedText = extracted_text
            record.rawExtraction = raw_extraction
            record.validatedExtraction = validated_extraction
            record.status = QuestionImportStatus.NEEDS_REVIEW
            record.completedAt = utc_now()
            record.updatedAt = utc_now()
            record.errorMessage = None
            record.errorCategory = None
            await s.commit()
            await s.refresh(record)
        return record

    if session:
        return await _do(session)
    async with db.get_session() as s:
        return await _do(s)


async def update_question_import_failure(
    import_id: str,
    error_category: str,
    error_message: str,
    session: AsyncSession | None = None,
) -> QuestionImport | None:
    """Marks an import as FAILED with a safe error category and sanitized message."""

    async def _do(s: AsyncSession):
        stmt = select(QuestionImport).where(QuestionImport.id == import_id)
        res = await s.execute(stmt)
        record = res.scalar_one_or_none()
        if record:
            record.status = QuestionImportStatus.FAILED
            record.errorCategory = error_category
            record.errorMessage = error_message
            record.updatedAt = utc_now()
            await s.commit()
            await s.refresh(record)
        return record

    if session:
        return await _do(session)
    async with db.get_session() as s:
        return await _do(s)


async def update_question_import_draft(
    import_id: str,
    validated_extraction: dict[str, Any],
    session: AsyncSession | None = None,
) -> QuestionImport | None:
    """Updates the editable draft while still in NEEDS_REVIEW."""

    async def _do(s: AsyncSession):
        stmt = select(QuestionImport).where(QuestionImport.id == import_id)
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


async def mark_question_import_completed(
    import_id: str,
    session: AsyncSession | None = None,
) -> QuestionImport | None:
    """Marks an import as COMPLETED upon successful confirmation."""

    async def _do(s: AsyncSession):
        stmt = select(QuestionImport).where(QuestionImport.id == import_id)
        res = await s.execute(stmt)
        record = res.scalar_one_or_none()
        if record:
            record.status = QuestionImportStatus.COMPLETED
            record.confirmedAt = utc_now()
            record.updatedAt = utc_now()
            await s.commit()
            await s.refresh(record)
        return record

    if session:
        return await _do(session)
    async with db.get_session() as s:
        return await _do(s)
