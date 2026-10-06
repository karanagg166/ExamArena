"""Answer-key upload size limits through the real router with external calls mocked."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

import app.answer_keys.router as answer_key_router
from app.core.config import settings
from app.core.models import (
    AnswerKeyImport,
    AnswerKeyImportSourceType,
    AnswerKeyImportStatus,
)
from app.storage.base import StoredFile


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "question_limit,answer_key_limit,file_size,expected_status",
    [
        (20, 1, 1024 * 1024, 202),
        (20, 1, 1024 * 1024 + 1, 413),
        (1, 2, 1024 * 1024 + 1, 202),
    ],
    ids=["at-answer-key-limit", "over-answer-key-limit", "over-question-limit-allowed"],
)
async def test_answer_key_upload_uses_its_own_size_limit(
    monkeypatch, question_limit, answer_key_limit, file_size, expected_status
):
    monkeypatch.setattr(settings, "QUESTION_IMPORT_MAX_FILE_MB", question_limit)
    monkeypatch.setattr(settings, "ANSWER_KEY_IMPORT_MAX_FILE_MB", answer_key_limit)
    monkeypatch.setattr(
        answer_key_router,
        "require_exam_answer_key_access",
        AsyncMock(
            return_value=(
                SimpleNamespace(id="teacher-id"),
                SimpleNamespace(id="exam-id"),
            )
        ),
    )
    storage = Mock()
    storage.save_file = AsyncMock(
        return_value=StoredFile(
            key="synthetic/key.pdf", provider="local", resource_type="raw"
        )
    )
    monkeypatch.setattr(answer_key_router, "get_storage_provider", lambda: storage)
    now = datetime.now(UTC)
    record = AnswerKeyImport(
        id="import-id",
        examId="exam-id",
        teacherId="teacher-id",
        originalFileName="key.pdf",
        fileType="application/pdf",
        fileSize=file_size,
        filePath="synthetic/key.pdf",
        status=AnswerKeyImportStatus.UPLOADED,
        sourceType=AnswerKeyImportSourceType.PDF_TEXT,
        createdAt=now,
        updatedAt=now,
    )
    create = AsyncMock(return_value=record)
    monkeypatch.setattr(answer_key_router.crud, "create_answer_key_import", create)
    monkeypatch.setattr(answer_key_router, "record_audit_event", AsyncMock())
    process = AsyncMock()
    monkeypatch.setattr(answer_key_router, "process_answer_key_import", process)

    app = FastAPI()
    app.include_router(answer_key_router.router)
    app.dependency_overrides[answer_key_router.get_current_user] = (
        lambda: SimpleNamespace(id="user-id")
    )
    header = b"%PDF-1.4\n"
    content = header + b"x" * (file_size - len(header))
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/exams/exam-id/answer-key-imports",
            files={"file": ("key.pdf", content, "application/pdf")},
        )

    assert response.status_code == expected_status
    if expected_status == 413:
        assert (
            response.json()["detail"]
            == f"File exceeds maximum allowed size of {answer_key_limit} MB"
        )
        storage.save_file.assert_not_awaited()
        create.assert_not_awaited()
        process.assert_not_awaited()
    else:
        assert response.json()["fileSize"] == file_size
        storage.save_file.assert_awaited_once()
        create.assert_awaited_once()
        process.assert_awaited_once_with(record.id)
