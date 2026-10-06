"""Regression tests for storage reads in both import workers; no network or database."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.ai.extraction import DocumentExtractionError
from app.answer_keys import service as answer_key_service
from app.imports import service as question_import_service
from app.storage.base import StorageReadError


@pytest.fixture(params=["answer_key", "question"])
def worker(request, monkeypatch):
    name = request.param
    service = answer_key_service if name == "answer_key" else question_import_service
    record = SimpleNamespace(
        id="import-id",
        status="UPLOADED",
        storageKey="examarena/imports/asset",
        filePath="legacy/path.pdf",
        storageResourceType=None,
        fileType="application/pdf",
        originalFileName="upload.pdf",
    )
    storage = Mock()
    storage.get_file = AsyncMock(return_value=b"synthetic document")
    monkeypatch.setattr(service, "get_storage_provider", lambda: storage)
    monkeypatch.setattr(
        service.crud, f"get_{name}_import_by_id", AsyncMock(return_value=record)
    )
    monkeypatch.setattr(
        service.crud, f"update_{name}_import_processing_start", AsyncMock()
    )
    failure = AsyncMock()
    monkeypatch.setattr(service.crud, f"update_{name}_import_failure", failure)
    # Stop after the real worker reads bytes; extraction/matching are outside this task.
    extract = Mock(side_effect=DocumentExtractionError("Stop after storage read"))
    monkeypatch.setattr(service, "extract_document_content", extract)
    return SimpleNamespace(
        process=getattr(service, f"process_{name}_import"),
        record=record,
        storage=storage,
        extract=extract,
        failure=failure,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mime,resource_type",
    [("application/pdf", "raw"), ("image/png", "image"), ("image/jpeg", "image")],
    ids=["pdf", "png", "jpeg"],
)
async def test_worker_uses_persisted_resource_type(worker, mime, resource_type):
    worker.record.fileType = mime
    worker.record.storageResourceType = resource_type

    await worker.process(worker.record.id)

    worker.storage.get_file.assert_awaited_once_with(
        worker.record.storageKey, resource_type=resource_type
    )
    worker.extract.assert_called_once_with(
        b"synthetic document", mime, filename=worker.record.originalFileName
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mime,resource_type",
    [("application/pdf", "raw"), ("image/png", "image"), ("image/jpeg", "image")],
    ids=["pdf", "png", "jpeg"],
)
async def test_worker_infers_legacy_null_resource_type(worker, mime, resource_type):
    worker.record.fileType = mime

    await worker.process(worker.record.id)

    worker.storage.get_file.assert_awaited_once_with(
        worker.record.storageKey, resource_type=resource_type
    )
    worker.extract.assert_called_once()


@pytest.mark.asyncio
async def test_worker_prefers_persisted_type_over_mime(worker):
    worker.record.storageResourceType = "image"
    worker.record.fileType = "application/octet-stream"

    await worker.process(worker.record.id)

    worker.storage.get_file.assert_awaited_once_with(
        worker.record.storageKey, resource_type="image"
    )


@pytest.mark.asyncio
async def test_worker_reads_legacy_file_path_when_storage_key_is_null(worker):
    worker.record.storageKey = None
    worker.record.fileType = "image/jpeg"

    await worker.process(worker.record.id)

    worker.storage.get_file.assert_awaited_once_with(
        worker.record.filePath, resource_type="image"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "resource_type,mime",
    [(None, "application/octet-stream"), ("auto", "image/png")],
    ids=["unknown-legacy-mime", "invalid-persisted-type"],
)
async def test_worker_fails_before_fetching_when_type_is_unknown(
    worker, resource_type, mime
):
    worker.record.storageResourceType = resource_type
    worker.record.fileType = mime

    await worker.process(worker.record.id)

    worker.storage.get_file.assert_not_awaited()
    worker.extract.assert_not_called()
    worker.failure.assert_awaited_once()
    assert worker.failure.call_args.kwargs["error_category"] == "STORAGE_READ"
    assert (
        "Cannot determine storage resource type"
        in worker.failure.call_args.kwargs["error_message"]
    )


@pytest.mark.asyncio
async def test_worker_reports_storage_read_failure(worker):
    worker.storage.get_file.side_effect = StorageReadError(
        "Asset could not be retrieved"
    )

    await worker.process(worker.record.id)

    worker.extract.assert_not_called()
    worker.failure.assert_awaited_once_with(
        worker.record.id,
        error_category="STORAGE_READ",
        error_message="Asset could not be retrieved",
    )
