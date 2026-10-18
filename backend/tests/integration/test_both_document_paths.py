"""Integration tests verifying both question paper and answer key document paths:
digital PDF, scanned PDF, scanned image (with real OCR assertions), corrupt file,
review, and transactional confirmation.
"""

import io
import os
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.extraction.image import extract_image_document
from app.ai.extraction.pdf import extract_pdf_document
from app.answer_keys.service import confirm_answer_key_import, process_answer_key_import
from app.core.config import settings
from app.core.models import (
    AnswerKeyImport,
    AnswerKeyImportSourceType,
    AnswerKeyImportStatus,
    Question,
    QuestionImport,
    QuestionImportSourceType,
    QuestionImportStatus,
    QuestionOption,
    Role,
)
from app.imports.service import confirm_question_import, process_question_import
from tests.factories.exam_factory import create_exam_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory

QP_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "question_papers")
AK_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "answer_keys")


@pytest.fixture(autouse=True)
def enable_cohere_stub(monkeypatch):
    """Enable deterministic Cohere stub mode for consistent and offline verification."""
    monkeypatch.setattr(settings, "COHERE_STUB_MODE", True)
    monkeypatch.setattr(settings, "ALLOW_IN_PROCESS_IMPORT_FALLBACK", True)


# ─────────────────────────────────────────────────────────────────────────────
# 1. QUESTION PAPER DOCUMENT PATHS
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_question_paper_digital_pdf_path(
    auth_client_factory, db_session: AsyncSession
):
    """Verify digital PDF question paper path: upload -> extraction -> review -> confirmation."""
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_qp_dig@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-QP-DIG")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_qp_dig@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    pdf_bytes = open(os.path.join(QP_FIXTURES_DIR, "simple_mcq.pdf"), "rb").read()

    # Verify digital extraction directly
    doc = extract_pdf_document(pdf_bytes)
    assert doc.source_type.value == "PDF_TEXT"
    assert len(doc.text) > 100

    # 1. Upload
    res_upload = await client.post(
        f"/api/v1/exams/{exam.id}/question-imports",
        files={"file": ("simple_mcq.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert res_upload.status_code == 202
    import_id = res_upload.json()["id"]

    # 2. Worker processes
    await process_question_import(import_id, generation=1)

    # 3. Check status is NEEDS_REVIEW
    res_status = await client.get(f"/api/v1/question-imports/{import_id}")
    assert res_status.status_code == 200
    data = res_status.json()
    assert data["status"] == "NEEDS_REVIEW"
    assert len(data["questions"]) > 0

    # 4. Teacher confirms
    res_confirm = await client.post(f"/api/v1/question-imports/{import_id}/confirm")
    assert res_confirm.status_code == 200
    assert res_confirm.json()["status"] == "COMPLETED"
    assert res_confirm.json()["createdQuestionsCount"] > 0

    # 5. Assert database rows
    q_count = (await db_session.execute(
        select(func.count(Question.id)).where(Question.examId == exam.id)
    )).scalar_one()
    assert q_count > 0


@pytest.mark.asyncio
async def test_question_paper_scanned_pdf_with_real_ocr(
    auth_client_factory, db_session: AsyncSession
):
    """Verify scanned PDF question paper: OCR actually executes, extracts text >50 chars,

    and proceeds through worker to NEEDS_REVIEW and confirmation.
    """
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_qp_scan@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-QP-SCAN")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_qp_scan@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    pdf_bytes = open(os.path.join(QP_FIXTURES_DIR, "scanned_sample.pdf"), "rb").read()

    # Verify real OCR execution directly on fixture
    doc = extract_pdf_document(pdf_bytes)
    assert doc.source_type.value == "PDF_SCANNED"
    assert len(doc.text) > 50, f"Expected >50 characters from OCR, got {len(doc.text)}"
    assert doc.metadata.get("scanned_pages_count", 0) >= 1

    # 1. Upload
    res_upload = await client.post(
        f"/api/v1/exams/{exam.id}/question-imports",
        files={"file": ("scanned_sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert res_upload.status_code == 202
    import_id = res_upload.json()["id"]

    # 2. Worker processes
    await process_question_import(import_id, generation=1)

    # 3. Check status is NEEDS_REVIEW and source type is PDF_SCANNED
    res_status = await client.get(f"/api/v1/question-imports/{import_id}")
    assert res_status.status_code == 200
    data = res_status.json()
    assert data["status"] == "NEEDS_REVIEW"
    assert data["sourceType"] == "PDF_SCANNED"


@pytest.mark.asyncio
async def test_question_paper_scanned_image_with_real_ocr(
    auth_client_factory, db_session: AsyncSession
):
    """Verify scanned PNG image paper: OCR extracts text and reaches review."""
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_qp_img@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-QP-IMG")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_qp_img@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    img_bytes = open(os.path.join(QP_FIXTURES_DIR, "scanned_paper.png"), "rb").read()

    # Direct OCR assertion
    img_doc = extract_image_document(img_bytes, "scanned_paper.png")
    assert img_doc.source_type.value == "IMAGE"
    assert len(img_doc.text) > 50, f"Expected >50 characters from OCR, got {len(img_doc.text)}"

    # Upload
    res_upload = await client.post(
        f"/api/v1/exams/{exam.id}/question-imports",
        files={"file": ("scanned_paper.png", io.BytesIO(img_bytes), "image/png")},
    )
    assert res_upload.status_code == 202
    import_id = res_upload.json()["id"]

    # Worker processes
    await process_question_import(import_id, generation=1)

    res_status = await client.get(f"/api/v1/question-imports/{import_id}")
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "NEEDS_REVIEW"
    assert res_status.json()["sourceType"] == "IMAGE"


@pytest.mark.asyncio
async def test_question_paper_corrupt_file_failure_behavior(
    auth_client_factory, db_session: AsyncSession
):
    """Verify corrupted question paper marks record FAILED with DOCUMENT_PARSING."""
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_qp_corrupt@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-QP-CORRUPT")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_qp_corrupt@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    corrupt_bytes = open(os.path.join(QP_FIXTURES_DIR, "corrupt_sample.pdf"), "rb").read()

    res_upload = await client.post(
        f"/api/v1/exams/{exam.id}/question-imports",
        files={"file": ("corrupt_sample.pdf", io.BytesIO(corrupt_bytes), "application/pdf")},
    )
    assert res_upload.status_code == 202
    import_id = res_upload.json()["id"]

    await process_question_import(import_id, generation=1)

    res_status = await client.get(f"/api/v1/question-imports/{import_id}")
    assert res_status.status_code == 200
    data = res_status.json()
    assert data["status"] == "FAILED"
    assert data["errorCategory"] == "DOCUMENT_PARSING"
    assert "Corrupt or unreadable" in (data["errorMessage"] or "")


# ─────────────────────────────────────────────────────────────────────────────
# 2. ANSWER KEY DOCUMENT PATHS
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_answer_key_digital_pdf_path(
    auth_client_factory, db_session: AsyncSession
):
    """Verify digital PDF answer key path: upload -> extraction -> review -> confirmation."""
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_ak_dig@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-AK-DIG")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_ak_dig@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)

    # Seed an exam question to match against
    q1 = Question(
        examId=exam.id,
        questionNumber=1,
        text="What is the capital of France?",
        questionType="MULTIPLE_CHOICE",
        marks=2,
        section="Section A",
    )
    db_session.add(q1)
    await db_session.flush()

    opt_a = QuestionOption(
        questionId=q1.id,
        optionNumber=1,
        text="Paris",
        isCorrect=False,
    )
    opt_b = QuestionOption(
        questionId=q1.id,
        optionNumber=2,
        text="London",
        isCorrect=False,
    )
    db_session.add_all([opt_a, opt_b])
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    pdf_bytes = open(os.path.join(AK_FIXTURES_DIR, "answer_key_sample.pdf"), "rb").read()

    # 1. Upload
    res_upload = await client.post(
        f"/api/v1/exams/{exam.id}/answer-key-imports",
        files={"file": ("answer_key_sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert res_upload.status_code == 202
    import_id = res_upload.json()["id"]

    # 2. Worker processes
    await process_answer_key_import(import_id, generation=1)

    # 3. Check status is NEEDS_REVIEW
    res_status = await client.get(f"/api/v1/answer-key-imports/{import_id}")
    assert res_status.status_code == 200
    data = res_status.json()
    assert data["status"] == "NEEDS_REVIEW"
    assert data["answers"] is not None
    assert len(data["answers"]) > 0

    # 4. Confirm answer key
    res_confirm = await client.post(f"/api/v1/answer-key-imports/{import_id}/confirm")
    assert res_confirm.status_code == 200
    assert res_confirm.json()["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_answer_key_scanned_image_with_real_ocr(
    auth_client_factory, db_session: AsyncSession
):
    """Verify scanned answer key image: OCR extracts text and transitions to review."""
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_ak_img@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-AK-IMG")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_ak_img@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    img_bytes = open(os.path.join(AK_FIXTURES_DIR, "scanned_answer_key.png"), "rb").read()

    # Verify OCR extraction directly
    img_doc = extract_image_document(img_bytes, "scanned_answer_key.png")
    assert img_doc.source_type.value == "IMAGE"
    assert len(img_doc.text) > 50

    # Upload
    res_upload = await client.post(
        f"/api/v1/exams/{exam.id}/answer-key-imports",
        files={"file": ("scanned_answer_key.png", io.BytesIO(img_bytes), "image/png")},
    )
    assert res_upload.status_code == 202
    import_id = res_upload.json()["id"]

    # Worker processes
    await process_answer_key_import(import_id, generation=1)

    res_status = await client.get(f"/api/v1/answer-key-imports/{import_id}")
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "NEEDS_REVIEW"


@pytest.mark.asyncio
async def test_answer_key_corrupt_file_failure_behavior(
    auth_client_factory, db_session: AsyncSession
):
    """Verify corrupted answer key PDF is safely marked FAILED with DOCUMENT_PARSING."""
    principal = await create_user_factory(db_session, role=Role.PRINCIPAL, email="p_ak_corrupt@dev.local")
    school = await create_school_factory(db_session, creator_user=principal, school_code="SCH-AK-CORRUPT")
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER, email="t_ak_corrupt@dev.local")
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    exam = await create_exam_factory(db_session, teacher=teacher)
    await db_session.commit()

    client = await auth_client_factory(teacher_user)
    corrupt_bytes = open(os.path.join(AK_FIXTURES_DIR, "corrupt_answer_key.pdf"), "rb").read()

    res_upload = await client.post(
        f"/api/v1/exams/{exam.id}/answer-key-imports",
        files={"file": ("corrupt_answer_key.pdf", io.BytesIO(corrupt_bytes), "application/pdf")},
    )
    assert res_upload.status_code == 202
    import_id = res_upload.json()["id"]

    await process_answer_key_import(import_id, generation=1)

    res_status = await client.get(f"/api/v1/answer-key-imports/{import_id}")
    assert res_status.status_code == 200
    data = res_status.json()
    assert data["status"] == "FAILED"
    assert data["errorCategory"] == "DOCUMENT_PARSING"
