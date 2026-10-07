"""Unit tests for CourseMaterialService business logic and failure compensation."""

import io
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException, UploadFile

from app.core.models import (
    CourseMaterial,
    CourseMaterialDocumentType,
    CourseMaterialStatus,
    Subject,
    generate_uuid,
)
from app.course_materials.service import CourseMaterialService, validate_material_file
from app.integrations.search_sphere.client import SearchSphereClient
from app.integrations.search_sphere.exceptions import (
    SearchSphereError,
    SearchSphereNotFoundError,
)


def test_validate_material_file():
    # Valid PDF
    valid_pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj"
    assert validate_material_file(valid_pdf, "book.pdf", "application/pdf") == "application/pdf"

    # Empty file
    with pytest.raises(HTTPException) as exc:
        validate_material_file(b"", "empty.pdf", "application/pdf")
    assert exc.value.status_code == 400
    assert "cannot be empty" in exc.value.detail

    # Non-PDF
    with pytest.raises(HTTPException) as exc:
        validate_material_file(b"NOT A PDF FILE", "notes.txt", "text/plain")
    assert exc.value.status_code == 400
    assert "Only PDF documents" in exc.value.detail


@pytest.mark.asyncio
async def test_upload_course_material_success(mocker):
    mock_ss = MagicMock(spec=SearchSphereClient)
    mock_ss.ensure_collection = AsyncMock(return_value={"collection_id": "subject_science"})
    mock_ss.upload_file = AsyncMock(
        return_value={"storage_key": "storage/path/notes.pdf", "mime_type": "application/pdf", "file_size": 100}
    )
    mock_ss.register_document = AsyncMock(
        return_value={"id": "ss_doc_123", "status": "PROCESSING"}
    )

    mock_session = AsyncMock()
    mock_created_material = MagicMock(spec=CourseMaterial)
    mock_created_material.id = "mat_abc"

    mock_updated_material = MagicMock(spec=CourseMaterial)
    mock_updated_material.id = "mat_abc"
    mock_updated_material.schoolId = "sch_1"
    mock_updated_material.subject = Subject.SCIENCE
    mock_updated_material.classId = None
    mock_updated_material.uploadedBy = "usr_teacher_1"
    mock_updated_material.title = "Physics Textbook"
    mock_updated_material.description = "Chapter 1"
    mock_updated_material.originalFileName = "physics.pdf"
    mock_updated_material.fileSize = 100
    mock_updated_material.mimeType = "application/pdf"
    mock_updated_material.documentType = CourseMaterialDocumentType.TEXTBOOK
    mock_updated_material.searchSphereDocumentId = "ss_doc_123"
    mock_updated_material.searchSphereCollectionId = "subject_science"
    mock_updated_material.status = CourseMaterialStatus.PROCESSING
    mock_updated_material.processingError = None
    mock_updated_material.createdAt = "2026-10-07T12:00:00Z"
    mock_updated_material.updatedAt = "2026-10-07T12:00:00Z"

    mocker.patch(
        "app.course_materials.crud.create_course_material",
        AsyncMock(return_value=mock_created_material),
    )
    mocker.patch(
        "app.course_materials.crud.update_course_material_status",
        AsyncMock(return_value=mock_updated_material),
    )

    service = CourseMaterialService(search_sphere_client=mock_ss)

    file_content = b"%PDF-1.5 test content"
    upload_file = UploadFile(filename="physics.pdf", file=io.BytesIO(file_content))

    res = await service.upload_course_material(
        session=mock_session,
        school_id="sch_1",
        uploaded_by_user_id="usr_teacher_1",
        subject=Subject.SCIENCE,
        title="Physics Textbook",
        file=upload_file,
        document_type=CourseMaterialDocumentType.TEXTBOOK,
        description="Chapter 1",
    )

    assert res.id == "mat_abc"
    assert res.search_sphere_document_id == "ss_doc_123"
    assert res.status == CourseMaterialStatus.PROCESSING

    # Verify Search-Sphere interactions
    mock_ss.ensure_collection.assert_awaited_once_with(
        collection_id="subject_science",
        name="SCIENCE Materials",
        description="Course materials for SCIENCE in school sch_1",
        tenant_id="school_sch_1",
    )
    mock_ss.upload_file.assert_awaited_once()
    mock_ss.register_document.assert_awaited_once()


@pytest.mark.asyncio
async def test_upload_course_material_failure_compensation(mocker):
    mock_ss = MagicMock(spec=SearchSphereClient)
    mock_ss.ensure_collection = AsyncMock(return_value={"collection_id": "subject_maths"})
    mock_ss.upload_file = AsyncMock(side_effect=SearchSphereError("Network failure uploading file"))

    mock_session = AsyncMock()
    mock_created = MagicMock(spec=CourseMaterial)
    mock_created.id = "mat_fail_1"

    mocker.patch(
        "app.course_materials.crud.create_course_material",
        AsyncMock(return_value=mock_created),
    )
    mock_update = mocker.patch(
        "app.course_materials.crud.update_course_material_status",
        AsyncMock(),
    )

    service = CourseMaterialService(search_sphere_client=mock_ss)
    file_content = b"%PDF-1.4 test"
    upload_file = UploadFile(filename="algebra.pdf", file=io.BytesIO(file_content))

    with pytest.raises(HTTPException) as exc_info:
        await service.upload_course_material(
            session=mock_session,
            school_id="sch_2",
            uploaded_by_user_id="usr_teacher_2",
            subject=Subject.MATHS,
            title="Algebra Notes",
            file=upload_file,
        )

    assert exc_info.value.status_code == 502
    assert "Search-Sphere" in exc_info.value.detail or "ingestion failed" in exc_info.value.detail

    # Verify failure compensation updated row status to FAILED
    mock_update.assert_awaited_once()
    call_kwargs = mock_update.await_args.kwargs
    assert call_kwargs["status"] == CourseMaterialStatus.FAILED
    assert "Network failure" in call_kwargs["processing_error"]


@pytest.mark.asyncio
async def test_refresh_status_success(mocker):
    mock_ss = MagicMock(spec=SearchSphereClient)
    mock_ss.get_document = AsyncMock(
        return_value={"id": "ss_doc_1", "status": "READY", "processing_error": None}
    )

    mock_material = MagicMock(spec=CourseMaterial)
    mock_material.id = "mat_1"
    mock_material.schoolId = "sch_1"
    mock_material.searchSphereDocumentId = "ss_doc_1"
    mock_material.status = CourseMaterialStatus.PROCESSING

    mocker.patch(
        "app.course_materials.crud.get_course_material_by_id",
        AsyncMock(return_value=mock_material),
    )
    mock_update = mocker.patch(
        "app.course_materials.crud.update_course_material_status",
        AsyncMock(return_value=mock_material),
    )

    service = CourseMaterialService(search_sphere_client=mock_ss)
    res = await service.refresh_status(
        session=AsyncMock(),
        material_id="mat_1",
        school_id="sch_1",
    )

    mock_ss.get_document.assert_awaited_once_with(
        document_id="ss_doc_1",
        tenant_id="school_sch_1",
    )
    mock_update.assert_awaited_once_with(
        session=mocker.ANY,
        material_id="mat_1",
        status=CourseMaterialStatus.READY,
        processing_error=None,
    )


@pytest.mark.asyncio
async def test_delete_course_material(mocker):
    mock_ss = MagicMock(spec=SearchSphereClient)
    mock_ss.delete_document = AsyncMock(return_value=True)

    mock_material = MagicMock(spec=CourseMaterial)
    mock_material.id = "mat_del"
    mock_material.schoolId = "sch_1"
    mock_material.searchSphereDocumentId = "ss_doc_del"

    mocker.patch(
        "app.course_materials.crud.get_course_material_by_id",
        AsyncMock(return_value=mock_material),
    )
    mock_crud_del = mocker.patch(
        "app.course_materials.crud.delete_course_material",
        AsyncMock(return_value=True),
    )

    service = CourseMaterialService(search_sphere_client=mock_ss)
    res = await service.delete_course_material(
        session=AsyncMock(),
        material_id="mat_del",
        school_id="sch_1",
    )
    assert res is True
    mock_ss.delete_document.assert_awaited_once_with(
        document_id="ss_doc_del",
        tenant_id="school_sch_1",
    )
    mock_crud_del.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_course_materials(mocker):
    mock_ss = MagicMock(spec=SearchSphereClient)
    mock_ss.search = AsyncMock(
        return_value={
            "query": "photosynthesis",
            "total": 1,
            "results": [
                {
                    "chunk_id": "chk_101",
                    "document_id": "ss_doc_101",
                    "text": "Photosynthesis produces glucose from sunlight.",
                    "score": 0.92,
                    "rank": 1,
                    "start_page": 12,
                    "end_page": 13,
                    "file_name": "biology.pdf",
                    "document_type": "TEXTBOOK",
                    "metadata": {"exam_arena_material_id": "mat_bio_1"},
                }
            ],
            "duration_ms": 22.5,
        }
    )

    service = CourseMaterialService(search_sphere_client=mock_ss)
    res = await service.search_materials(
        school_id="sch_alpha",
        query="photosynthesis",
        subject=Subject.SCIENCE,
        limit=5,
    )

    assert res.total == 1
    assert res.results[0].chunk_id == "chk_101"
    assert res.results[0].material_id == "mat_bio_1"
    assert res.results[0].start_page == 12

    mock_ss.search.assert_awaited_once_with(
        query="photosynthesis",
        collection_id="subject_science",
        limit=5,
        document_type=None,
        tenant_id="school_sch_alpha",
    )
