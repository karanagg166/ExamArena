import io
import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock
from app.ai.extraction.question_paper import (
    merge_and_deduplicate_questions,
)
from app.ai.extraction.pdf import extract_pdf_document, MAX_PDF_PAGES
from app.ai.extraction.document import DocumentExtractionError, DocumentSourceType
from app.ai.schemas.question_paper import (
    ExtractedOption,
    ExtractedQuestion,
    ExtractedQuestionPaper,
    ExtractedQuestionType,
)
from app.imports.service import confirm_question_import
from app.users.schemas import UserResponse
from app.core.models import Role


def test_merge_and_deduplicate_preserves_distinct_questions_with_long_prefix():
    """Two different questions sharing a long stem (>120 chars) must BOTH be retained."""
    long_passage = (
        "The standard model of particle physics is a relativistic quantum field theory "
        "formulated within the framework of gauge theories with local symmetry group "
        "SU(3)_C x SU(2)_L x U(1)_Y describing the electromagnetic, weak, and strong nuclear interactions. "
        "Based on this theoretical foundation, answer the following inquiry: "
    )

    q1 = ExtractedQuestion(
        question_number="1",
        question_type=ExtractedQuestionType.SHORT_ANSWER,
        text=long_passage + "Calculate the total decay width of the W boson.",
        marks=5.0,
        section="Section A",
    )

    q2 = ExtractedQuestion(
        question_number="2",
        question_type=ExtractedQuestionType.SHORT_ANSWER,
        text=long_passage + "Explain spontaneous symmetry breaking via the Brout-Englert-Higgs mechanism.",
        marks=5.0,
        section="Section A",
    )

    result = merge_and_deduplicate_questions([q1, q2])
    assert len(result) == 2, "Both distinct questions sharing a long prefix must be preserved!"
    assert result[0].question_number == "1"
    assert result[1].question_number == "2"


def test_merge_and_deduplicate_removes_genuine_duplicates():
    """Identical questions extracted in overlapping chunks must be deduplicated to one entry."""
    q_stem = "Explain the fundamental difference between TCP and UDP transport protocols."

    q_chunk1 = ExtractedQuestion(
        question_number="4",
        question_type=ExtractedQuestionType.ESSAY,
        text=q_stem,
        marks=None,
        section="Section B",
    )

    q_chunk2 = ExtractedQuestion(
        question_number="4",
        question_type=ExtractedQuestionType.ESSAY,
        text=q_stem,
        marks=10.0,
        section="Section B",
    )

    result = merge_and_deduplicate_questions([q_chunk1, q_chunk2])
    assert len(result) == 1, "Duplicate question must be merged into one"
    # Should retain the richer entry with marks populated
    assert result[0].marks == 10.0


def test_merge_and_deduplicate_preserves_different_sections():
    """Questions with identical text in different sections must both be preserved."""
    q1 = ExtractedQuestion(
        question_number="1",
        question_type=ExtractedQuestionType.SHORT_ANSWER,
        text="Define acceleration.",
        section="Section A",
    )
    q2 = ExtractedQuestion(
        question_number="1",
        question_type=ExtractedQuestionType.SHORT_ANSWER,
        text="Define acceleration.",
        section="Section B",
    )

    result = merge_and_deduplicate_questions([q1, q2])
    assert len(result) == 2


@pytest.mark.asyncio
async def test_confirm_question_import_rejects_fractional_marks(mocker):
    """confirm_question_import must reject fractional marks (e.g. 0.5, 1.5) with HTTP 400 instead of silently rounding to 0."""
    mock_import_record = MagicMock()
    mock_import_record.id = "imp-1"
    mock_import_record.examId = "exam-1"
    mock_import_record.status = "NEEDS_REVIEW"
    mock_import_record.validatedExtraction = {
        "title": "Test Paper",
        "questions": [
            {
                "question_number": "1",
                "question_type": "SHORT_ANSWER",
                "text": "What is the unit of force?",
                "marks": 0.5,  # Fractional marks that would have rounded to 0
                "options": [],
                "section": "Section A",
            }
        ],
    }

    mocker.patch("app.imports.crud.get_question_import_by_id", return_value=mock_import_record)

    mock_user = MagicMock(spec=UserResponse)
    mock_user.id = "usr-1"
    mock_user.role = Role.TEACHER

    with pytest.raises(HTTPException) as exc_info:
        await confirm_question_import("imp-1", mock_user)

    assert exc_info.value.status_code == 400
    assert "fractional marks" in exc_info.value.detail.lower()
    assert "0.5" in exc_info.value.detail


def test_extract_pdf_document_page_limit_enforced():
    """PDFs exceeding 50 pages must raise DocumentExtractionError."""
    # Mock pdfplumber with 51 pages
    mock_pdf = MagicMock()
    mock_pdf.pages = [MagicMock() for _ in range(MAX_PDF_PAGES + 1)]
    mock_open = MagicMock()
    mock_open.__enter__.return_value = mock_pdf

    import pdfplumber
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(pdfplumber, "open", lambda *a, **kw: mock_open)
        with pytest.raises(DocumentExtractionError, match="maximum supported limit"):
            extract_pdf_document(b"%PDF-1.4 mock")


def test_extract_pdf_document_scanned_ocr_fallback(mocker):
    """Scanned page with no digital text must trigger OCR fallback."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = ""  # No digital text
    mock_page.images = [MagicMock()]

    mock_img_obj = MagicMock()
    mock_img_obj.original = MagicMock()
    mock_page.to_image.return_value = mock_img_obj

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_open = MagicMock()
    mock_open.__enter__.return_value = mock_pdf

    import pdfplumber
    mocker.patch.object(pdfplumber, "open", return_value=mock_open)
    mocker.patch("pytesseract.image_to_string", return_value="OCR Extracted Question 1: What is DNA?")

    doc = extract_pdf_document(b"%PDF-1.4 fake")
    assert "OCR Extracted Question 1" in doc.text
    assert doc.source_type == DocumentSourceType.PDF_SCANNED
