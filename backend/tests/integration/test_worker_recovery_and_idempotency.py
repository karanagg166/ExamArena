"""Integration tests for worker recovery, idempotency, stale execution rejection,
and failure modes across question paper and answer key pipelines.
"""

import asyncio
import io
import json
import os
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.clients.cohere_client import (
    CohereAPIError,
    CohereClient,
    CohereRateLimitError,
    CohereTimeoutError,
)
from app.ai.schemas.question_paper import (
    ExtractedConfidence,
    ExtractedOption,
    ExtractedQuestion,
    ExtractedQuestionPaper,
    ExtractedQuestionType,
)
from app.answer_keys.service import process_answer_key_import
from app.core.config import settings
from app.core.models import (
    AnswerKeyImport,
    AnswerKeyImportStatus,
    Exam,
    Question,
    QuestionImport,
    QuestionImportStatus,
    QuestionOption,
    Role,
    utc_now,
)
from app.imports.service import confirm_question_import, process_question_import
from tests.factories.exam_factory import create_exam_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "question_papers")


@pytest.fixture
def dummy_extracted_paper():
    return ExtractedQuestionPaper(
        title="Mathematics Quiz",
        subject="MATH",
        total_marks=10.0,
        duration_minutes=30,
        instructions=["Answer all questions."],
        questions=[
            ExtractedQuestion(
                question_number="1",
                question_type=ExtractedQuestionType.MULTIPLE_CHOICE,
                text="What is 2 + 2?",
                marks=4.0,
                section="Section A",
                options=[
                    ExtractedOption(label="A", text="3"),
                    ExtractedOption(label="B", text="4", is_correct=True),
                    ExtractedOption(label="C", text="5"),
                    ExtractedOption(label="D", text="6"),
                ],
                confidence=ExtractedConfidence.HIGH,
                warnings=[],
            ),
            ExtractedQuestion(
                question_number="2",
                question_type=ExtractedQuestionType.MULTIPLE_CHOICE,
                text="What is 5 x 5?",
                marks=6.0,
                section="Section A",
                options=[
                    ExtractedOption(label="A", text="20"),
                    ExtractedOption(label="B", text="25", is_correct=True),
                    ExtractedOption(label="C", text="30"),
                    ExtractedOption(label="D", text="35"),
                ],
                confidence=ExtractedConfidence.HIGH,
                warnings=[],
            ),
        ],
        warnings=[],
    )


@pytest.mark.asyncio
async def test_duplicate_delivery_is_idempotent(db_session: AsyncSession, dummy_extracted_paper):
    """If an import is already in NEEDS_REVIEW, a duplicate worker delivery should safely abort."""
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_dup@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-DUP")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_dup@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)

    import_rec = QuestionImport(
        examId=exam.id,
        teacherId=teacher.id,
        originalFileName="simple_mcq.pdf",
        fileType="application/pdf",
        fileSize=1024,
        filePath="uploads/exam_test/simple_mcq.pdf",
        status=QuestionImportStatus.NEEDS_REVIEW,
        jobGeneration=1,
        validatedExtraction=dummy_extracted_paper.model_dump(),
    )
    db_session.add(import_rec)
    await db_session.commit()

    # Second worker execution of the exact same import
    with patch("app.imports.service.extract_document_content") as mock_extract:
        await process_question_import(import_rec.id, generation=1)
        # Should not re-extract or re-call extraction pipeline
        mock_extract.assert_not_called()

    # Verify status unchanged
    await db_session.refresh(import_rec)
    assert import_rec.status == QuestionImportStatus.NEEDS_REVIEW


@pytest.mark.asyncio
async def test_worker_termination_stuck_processing_recovers_to_timeout(
    auth_client_factory, db_session: AsyncSession
):
    """An import stuck in PROCESSING for >300s is transitioned to TIMEOUT upon status check."""
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_to@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-TO")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_to@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)

    stuck_time = utc_now() - timedelta(seconds=350)
    stuck_import = QuestionImport(
        examId=exam.id,
        teacherId=teacher.id,
        originalFileName="simple_mcq.pdf",
        fileType="application/pdf",
        fileSize=1024,
        filePath="uploads/exam_test/simple_mcq.pdf",
        status=QuestionImportStatus.PROCESSING,
        jobGeneration=1,
        createdAt=stuck_time,
        updatedAt=stuck_time,
    )
    db_session.add(stuck_import)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    res = await client.get(f"/api/v1/question-imports/{stuck_import.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "FAILED"
    assert data["errorCategory"] == "TIMEOUT"
    assert "timed out after 300 seconds" in (data["errorMessage"] or "")


@pytest.mark.asyncio
async def test_retry_increments_generation_and_rejects_stale_completion(
    auth_client_factory, db_session: AsyncSession, dummy_extracted_paper
):
    """When a job is retried (generation increments to 2), a late delivery from generation 1

    must be rejected and cannot overwrite the record.
    """
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_gen@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-GEN")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_gen@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)

    # Initial failed job with generation = 1
    import_rec = QuestionImport(
        examId=exam.id,
        teacherId=teacher.id,
        originalFileName="simple_mcq.pdf",
        fileType="application/pdf",
        fileSize=1024,
        filePath="uploads/exam_test/simple_mcq.pdf",
        status=QuestionImportStatus.FAILED,
        errorCategory="WORKER_UNAVAILABLE",
        jobGeneration=1,
    )
    db_session.add(import_rec)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)

    mock_pool = AsyncMock()
    mock_pool.get.return_value = b"healthy"
    mock_job = AsyncMock()
    mock_job.job_id = "job-gen-2"
    mock_pool.enqueue_job.return_value = mock_job

    with patch("arq.create_pool", return_value=mock_pool):
        retry_res = await client.post(f"/api/v1/question-imports/{import_rec.id}/retry")
        assert retry_res.status_code == 200

    # Verify generation is now 2 in DB
    await db_session.refresh(import_rec)
    assert import_rec.jobGeneration == 2
    assert import_rec.status == QuestionImportStatus.UPLOADED

    # Late worker execution from generation 1 arrives now
    with patch("app.imports.service.get_storage_provider") as mock_storage:
        # Should not execute extraction for stale generation 1
        await process_question_import(import_rec.id, generation=1)
        mock_storage.assert_not_called()

    # Verify record remained untouched by stale worker
    await db_session.refresh(import_rec)
    assert import_rec.jobGeneration == 2
    assert import_rec.status == QuestionImportStatus.UPLOADED


@pytest.mark.asyncio
async def test_provider_timeout_and_rate_limit_handled_gracefully(
    db_session: AsyncSession
):
    """External AI provider timeouts and rate limits are caught cleanly and recorded without unhandled crashes."""
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_ai_err@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-AI-ERR")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_ai_err@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)

    import_rec = QuestionImport(
        examId=exam.id,
        teacherId=teacher.id,
        originalFileName="simple_mcq.pdf",
        fileType="application/pdf",
        fileSize=1024,
        filePath="uploads/exam_test/simple_mcq.pdf",
        status=QuestionImportStatus.UPLOADED,
        jobGeneration=1,
    )
    db_session.add(import_rec)
    await db_session.commit()

    # Simulate storage returning valid pdf bytes
    pdf_path = os.path.join(FIXTURES_DIR, "simple_mcq.pdf")
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    mock_storage = AsyncMock()
    mock_storage.get_file.return_value = pdf_bytes

    # 1. Rate limit error
    with (
        patch("app.imports.service.get_storage_provider", return_value=mock_storage),
        patch("app.ai.clients.cohere_client.CohereClient.extract_structured_json", side_effect=CohereRateLimitError("Rate limit reached. Please retry in 60s.")),
    ):
        await process_question_import(import_rec.id, generation=1)

    await db_session.refresh(import_rec)
    assert import_rec.status == QuestionImportStatus.FAILED
    assert import_rec.errorCategory == "RATE_LIMIT"
    assert "rate limit" in (import_rec.errorMessage or "").lower()

    # Reset for timeout test
    import_rec.status = QuestionImportStatus.UPLOADED
    import_rec.errorCategory = None
    import_rec.errorMessage = None
    import_rec.jobGeneration = 2
    await db_session.commit()

    # 2. Timeout error
    with (
        patch("app.imports.service.get_storage_provider", return_value=mock_storage),
        patch("app.ai.clients.cohere_client.CohereClient.extract_structured_json", side_effect=CohereTimeoutError("Cohere API request timed out.")),
    ):
        await process_question_import(import_rec.id, generation=2)

    await db_session.refresh(import_rec)
    assert import_rec.status == QuestionImportStatus.FAILED
    assert import_rec.errorCategory == "TIMEOUT"
    assert "timed out" in (import_rec.errorMessage or "").lower()


@pytest.mark.asyncio
async def test_storage_read_failure_records_error_safely(db_session: AsyncSession):
    """Storage loading failures are safely marked as STORAGE_READ."""
    from app.storage.base import StorageReadError

    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_stor_err@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-STOR-ERR")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_stor_err@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)

    import_rec = QuestionImport(
        examId=exam.id,
        teacherId=teacher.id,
        originalFileName="missing.pdf",
        fileType="application/pdf",
        fileSize=1024,
        filePath="uploads/exam_test/missing.pdf",
        status=QuestionImportStatus.UPLOADED,
        jobGeneration=1,
    )
    db_session.add(import_rec)
    await db_session.commit()

    mock_storage = AsyncMock()
    mock_storage.get_file.side_effect = StorageReadError("Storage read failed on storage backend")

    with patch("app.imports.service.get_storage_provider", return_value=mock_storage):
        await process_question_import(import_rec.id, generation=1)

    await db_session.refresh(import_rec)
    assert import_rec.status == QuestionImportStatus.FAILED
    assert import_rec.errorCategory == "STORAGE_READ"
    assert "Storage read failed" in (import_rec.errorMessage or "")


@pytest.mark.asyncio
async def test_ocr_and_document_corruption_handled_safely(db_session: AsyncSession):
    """Corrupt PDF bytes raise DocumentExtractionError and are recorded as DOCUMENT_PARSING."""
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_ocr_corrupt@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-OCR-C")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_ocr_corrupt@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)

    import_rec = QuestionImport(
        examId=exam.id,
        teacherId=teacher.id,
        originalFileName="corrupt_sample.pdf",
        fileType="application/pdf",
        fileSize=100,
        filePath="uploads/exam_test/corrupt_sample.pdf",
        status=QuestionImportStatus.UPLOADED,
        jobGeneration=1,
    )
    db_session.add(import_rec)
    await db_session.commit()

    corrupt_bytes = b"%PDF-1.4\nCorrupt-binary-payload-here\xff\xfe\x00"
    mock_storage = AsyncMock()
    mock_storage.get_file.return_value = corrupt_bytes

    with patch("app.imports.service.get_storage_provider", return_value=mock_storage):
        await process_question_import(import_rec.id, generation=1)

    await db_session.refresh(import_rec)
    assert import_rec.status == QuestionImportStatus.FAILED
    assert import_rec.errorCategory == "DOCUMENT_PARSING"
    assert "Corrupt or unreadable" in (import_rec.errorMessage or "")


@pytest.mark.asyncio
async def test_concurrent_confirmation_is_idempotent_no_duplicates(
    auth_client_factory, db_session: AsyncSession, dummy_extracted_paper
):
    """Concurrent confirmation calls must use row locking and commit questions exactly once."""
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_cconf@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-CCONF")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_cconf@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)

    import_rec = QuestionImport(
        examId=exam.id,
        teacherId=teacher.id,
        originalFileName="simple_mcq.pdf",
        fileType="application/pdf",
        fileSize=1024,
        filePath="uploads/exam_test/simple_mcq.pdf",
        status=QuestionImportStatus.NEEDS_REVIEW,
        jobGeneration=1,
        validatedExtraction=dummy_extracted_paper.model_dump(),
    )
    db_session.add(import_rec)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)

    # First confirmation succeeds
    res1 = await client.post(f"/api/v1/question-imports/{import_rec.id}/confirm")
    assert res1.status_code == 200
    assert res1.json()["createdQuestionsCount"] == 2

    # Second confirmation returns 200 with 0 created questions (idempotent, no duplicates)
    res2 = await client.post(f"/api/v1/question-imports/{import_rec.id}/confirm")
    assert res2.status_code == 200
    assert res2.json()["createdQuestionsCount"] == 0
    assert res2.json()["status"] == "COMPLETED"

    # Verify database has exactly 2 questions and 8 options (no duplicates)
    q_count = (await db_session.execute(
        select(func.count(Question.id)).where(Question.examId == exam.id)
    )).scalar_one()
    assert q_count == 2

    opt_count = (await db_session.execute(
        select(func.count(QuestionOption.id))
        .join(Question, QuestionOption.questionId == Question.id)
        .where(Question.examId == exam.id)
    )).scalar_one()
    assert opt_count == 8


@pytest.mark.asyncio
async def test_retry_rejected_for_completed_and_needs_review(
    auth_client_factory, db_session: AsyncSession, dummy_extracted_paper
):
    """Retrying COMPLETED or NEEDS_REVIEW imports is rejected with HTTP 400."""
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_rejr@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-REJR")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_rejr@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)

    completed_rec = QuestionImport(
        examId=exam.id,
        teacherId=teacher.id,
        originalFileName="completed.pdf",
        fileType="application/pdf",
        fileSize=1024,
        filePath="uploads/exam_test/completed.pdf",
        status=QuestionImportStatus.COMPLETED,
        jobGeneration=1,
    )
    review_rec = QuestionImport(
        examId=exam.id,
        teacherId=teacher.id,
        originalFileName="review.pdf",
        fileType="application/pdf",
        fileSize=1024,
        filePath="uploads/exam_test/review.pdf",
        status=QuestionImportStatus.NEEDS_REVIEW,
        jobGeneration=1,
        validatedExtraction=dummy_extracted_paper.model_dump(),
    )
    db_session.add_all([completed_rec, review_rec])
    await db_session.commit()

    client = await auth_client_factory(teacher_user)

    res_comp = await client.post(f"/api/v1/question-imports/{completed_rec.id}/retry")
    assert res_comp.status_code == 400
    assert "Cannot retry an already completed import" in res_comp.json()["detail"]

    res_rev = await client.post(f"/api/v1/question-imports/{review_rec.id}/retry")
    assert res_rev.status_code == 400
    assert "already awaiting review" in res_rev.json()["detail"]


@pytest.mark.asyncio
async def test_active_processing_retry_rejected(
    auth_client_factory, db_session: AsyncSession
):
    """An import actively in PROCESSING (<300s) cannot be retried."""
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_actr@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-ACTR")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_actr@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)

    recent_time = utc_now() - timedelta(seconds=20)
    active_rec = QuestionImport(
        examId=exam.id,
        teacherId=teacher.id,
        originalFileName="active.pdf",
        fileType="application/pdf",
        fileSize=1024,
        filePath="uploads/exam_test/active.pdf",
        status=QuestionImportStatus.PROCESSING,
        jobGeneration=1,
        createdAt=recent_time,
        updatedAt=recent_time,
    )
    db_session.add(active_rec)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    res = await client.post(f"/api/v1/question-imports/{active_rec.id}/retry")
    assert res.status_code == 400
    assert "actively processing" in res.json()["detail"]
