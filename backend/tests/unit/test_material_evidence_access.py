"""Never return answer text or passages whose source authorization failed."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.core.models import CourseMaterialDocumentType, CourseMaterialStatus, Subject
from app.course_materials.service import CourseMaterialService


def material(**changes):
    return SimpleNamespace(**{**dict(id="public-material", searchSphereDocumentId="upstream-material", schoolId="school-a",
        subject=Subject.SCIENCE, classId="class-a", status=CourseMaterialStatus.READY,
        documentType=CourseMaterialDocumentType.TEXTBOOK, title="Public synthetic textbook", originalFileName="public.pdf"), **changes})


@pytest.mark.asyncio
@pytest.mark.parametrize("changes", [{"schoolId": "school-b"}, {"classId": "class-b"}, {"subject": Subject.MATHS},
    {"status": CourseMaterialStatus.FAILED}, {"id": "unknown", "searchSphereDocumentId": "unknown-upstream"}])
async def test_unverified_citation_rejects_the_entire_answer(mocker, changes):
    upstream = SimpleNamespace(generate_answer=AsyncMock(return_value={"answer": "UNAUTHORIZED SYNTHETIC EVIDENCE [1]",
        "citations": [{"document_id": "public-material", "chunk_id": "chunk-1", "citation_number": 1,
            "text_snippet": "UNAUTHORIZED SYNTHETIC EVIDENCE", "page_number": 1}], "retrieved_chunk_count": 1}))
    mocker.patch("app.course_materials.crud.get_course_materials_by_ids", AsyncMock(return_value=[material(**changes)]))
    service = CourseMaterialService(search_sphere_client=upstream)
    with pytest.raises(HTTPException) as failure:
        await service.answer_question(session=AsyncMock(), school_id="school-a", class_id="class-a", query="public", subject=Subject.SCIENCE)
    assert failure.value.status_code == 502
    assert "UNAUTHORIZED" not in str(failure.value.detail)


@pytest.mark.asyncio
async def test_unknown_search_result_is_not_returned(mocker):
    upstream = SimpleNamespace(search=AsyncMock(return_value={"results": [{"document_id": "missing", "chunk_id": "chunk-1",
        "text": "UNVERIFIED SYNTHETIC PASSAGE", "score": 0.9, "rank": 1}]}))
    mocker.patch("app.course_materials.crud.get_course_materials_by_ids", AsyncMock(return_value=[]))
    with pytest.raises(HTTPException) as failure:
        await CourseMaterialService(search_sphere_client=upstream).search_materials(session=AsyncMock(),
            school_id="school-a", class_id="class-a", query="public", subject=Subject.SCIENCE)
    assert failure.value.status_code == 502 and "UNVERIFIED" not in str(failure.value.detail)


@pytest.mark.asyncio
async def test_fabricated_citation_number_is_rejected(mocker):
    upstream = SimpleNamespace(generate_answer=AsyncMock(return_value={"answer": "PUBLIC SYNTHETIC CLAIM [9]",
        "citations": [{"document_id": "public-material", "chunk_id": "chunk-1", "citation_number": 1,
            "text_snippet": "PUBLIC SYNTHETIC CLAIM", "page_number": 1}], "retrieved_chunk_count": 1}))
    mocker.patch("app.course_materials.crud.get_course_materials_by_ids", AsyncMock(return_value=[material()]))
    with pytest.raises(HTTPException) as failure:
        await CourseMaterialService(search_sphere_client=upstream).answer_question(session=AsyncMock(), school_id="school-a",
            class_id="class-a", query="public", subject=Subject.SCIENCE)
    assert failure.value.status_code == 502 and "SYNTHETIC CLAIM" not in failure.value.detail


@pytest.mark.asyncio
async def test_uncited_upstream_text_is_replaced_with_deterministic_no_evidence_response():
    upstream = SimpleNamespace(generate_answer=AsyncMock(return_value={"answer": "UNSUPPORTED SYNTHETIC CLAIM",
        "citations": [], "retrieved_chunk_count": 3}))
    result = await CourseMaterialService(search_sphere_client=upstream).answer_question(session=AsyncMock(), school_id="school-a",
        class_id="class-a", query="public", subject=Subject.SCIENCE)
    assert "UNSUPPORTED" not in result.answer and result.retrieved_chunk_count == 0
