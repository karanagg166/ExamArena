"""Unit tests for digital PDF and image extraction."""

import os

import pytest

from app.ai.extraction.document import (
    DocumentExtractionError,
    DocumentSourceType,
)
from app.ai.extraction.image import extract_image_document
from app.ai.extraction.pdf import extract_pdf_document
from app.ai.extraction.question_paper import extract_document_content

FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "question_papers"
)
MATRIX_FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "pdf_matrix"
)


def _read_matrix_fixture(filename: str) -> bytes:
    path = os.path.join(MATRIX_FIXTURES_DIR, filename)
    with open(path, "rb") as f:
        return f.read()


def test_extract_one_page_digital_pdf():
    pdf_bytes = _read_matrix_fixture("one_page_digital.pdf")
    doc = extract_pdf_document(pdf_bytes)
    assert doc.source_type == DocumentSourceType.PDF_TEXT
    assert doc.page_count == 1
    assert "Digital Medical Summary" in doc.text
    assert "Patient ID: pat_12345" in doc.text


def test_extract_multipage_digital_pdf():
    pdf_bytes = _read_matrix_fixture("multipage_digital.pdf")
    doc = extract_pdf_document(pdf_bytes)
    assert doc.source_type == DocumentSourceType.PDF_TEXT
    assert doc.page_count == 3
    assert len(doc.pages) == 3
    assert "Page 1" in doc.text
    assert "Page 2" in doc.text
    assert "Page 3" in doc.text


def test_extract_tables_pdf():
    pdf_bytes = _read_matrix_fixture("tables.pdf")
    doc = extract_pdf_document(pdf_bytes)
    assert doc.source_type == DocumentSourceType.PDF_TEXT
    assert "Hemoglobin" in doc.text
    assert "Platelets" in doc.text
    assert "WBC Count" in doc.text


def test_extract_question_paper_single_mcq():
    pdf_bytes = _read_matrix_fixture("question_paper_single_mcq.pdf")
    doc = extract_pdf_document(pdf_bytes)
    assert doc.source_type == DocumentSourceType.PDF_TEXT
    assert "electric capacitance" in doc.text
    assert "Farad" in doc.text
    assert "Faraday Law" in doc.text


def test_extract_question_paper_multi_select():
    pdf_bytes = _read_matrix_fixture("question_paper_multi_select.pdf")
    doc = extract_pdf_document(pdf_bytes)
    assert doc.source_type == DocumentSourceType.PDF_TEXT
    assert "non-volatile storage" in doc.text
    assert "NAND Flash" in doc.text
    assert "cache replacement" in doc.text


def test_extract_answer_key_multi_correct():
    pdf_bytes = _read_matrix_fixture("answer_key_multi_correct.pdf")
    doc = extract_pdf_document(pdf_bytes)
    assert doc.source_type == DocumentSourceType.PDF_TEXT
    assert "MULTIPLE_CHOICE" in doc.text
    assert "Q5" in doc.text
    assert "A, B, D" in doc.text


def test_extract_subjective_paper_rubric():
    pdf_bytes = _read_matrix_fixture("subjective_paper_rubric.pdf")
    doc = extract_pdf_document(pdf_bytes)
    assert doc.source_type == DocumentSourceType.PDF_TEXT
    assert "ACID properties" in doc.text
    assert "Marking Rubric" in doc.text
    assert "Atomicity" in doc.text


def test_extract_unicode_multilingual():
    pdf_bytes = _read_matrix_fixture("unicode_multilingual.pdf")
    doc = extract_pdf_document(pdf_bytes)
    assert doc.source_type == DocumentSourceType.PDF_TEXT
    assert "μg/mL" in doc.text or "ug/mL" in doc.text or "37°C" in doc.text


def test_extract_embedded_images():
    pdf_bytes = _read_matrix_fixture("embedded_images.pdf")
    doc = extract_pdf_document(pdf_bytes)
    assert doc.page_count >= 1
    assert any(p.has_images for p in doc.pages)


def test_extract_scanned_image_only():
    pdf_bytes = _read_matrix_fixture("scanned_image_only.pdf")
    doc = extract_pdf_document(pdf_bytes)
    assert doc.page_count == 1
    # When digital characters are 0, source_type is PDF_SCANNED
    assert doc.source_type == DocumentSourceType.PDF_SCANNED


def test_extract_mixed_digital_scanned():
    pdf_bytes = _read_matrix_fixture("mixed_digital_scanned.pdf")
    doc = extract_pdf_document(pdf_bytes)
    assert doc.page_count == 2
    assert "Digital Intake Sheet" in doc.text


def test_extract_excessive_pages_limit_rejected():
    pdf_bytes = _read_matrix_fixture("excessive_pages.pdf")
    with pytest.raises(DocumentExtractionError) as exc_info:
        extract_pdf_document(pdf_bytes)
    assert "maximum supported limit of 50 pages" in str(exc_info.value)


def test_extract_corrupt_xref_rejected():
    pdf_bytes = _read_matrix_fixture("corrupt_xref.pdf")
    with pytest.raises(DocumentExtractionError) as exc_info:
        extract_pdf_document(pdf_bytes)
    assert (
        "corrupt" in str(exc_info.value).lower()
        or "unreadable" in str(exc_info.value).lower()
    )


def test_extract_truncated_pdf_rejected():
    pdf_bytes = _read_matrix_fixture("truncated.pdf")
    with pytest.raises(DocumentExtractionError) as exc_info:
        extract_pdf_document(pdf_bytes)
    assert (
        "corrupt" in str(exc_info.value).lower()
        or "unreadable" in str(exc_info.value).lower()
    )


def test_extract_fake_magic_bytes_rejected():
    pdf_bytes = _read_matrix_fixture("fake_magic_bytes.pdf")
    with pytest.raises(DocumentExtractionError) as exc_info:
        extract_pdf_document(pdf_bytes)
    assert (
        "corrupt" in str(exc_info.value).lower()
        or "unreadable" in str(exc_info.value).lower()
    )


def test_extract_renamed_pe_rejected():
    pdf_bytes = _read_matrix_fixture("renamed_pe.pdf")
    with pytest.raises(DocumentExtractionError) as exc_info:
        extract_pdf_document(pdf_bytes)
    assert (
        "corrupt" in str(exc_info.value).lower()
        or "unreadable" in str(exc_info.value).lower()
    )


def test_extract_renamed_elf_rejected():
    pdf_bytes = _read_matrix_fixture("renamed_elf.pdf")
    with pytest.raises(DocumentExtractionError) as exc_info:
        extract_pdf_document(pdf_bytes)
    assert (
        "corrupt" in str(exc_info.value).lower()
        or "unreadable" in str(exc_info.value).lower()
    )


def test_extract_renamed_zip_rejected():
    pdf_bytes = _read_matrix_fixture("renamed_zip.pdf")
    with pytest.raises(DocumentExtractionError) as exc_info:
        extract_pdf_document(pdf_bytes)
    assert (
        "corrupt" in str(exc_info.value).lower()
        or "unreadable" in str(exc_info.value).lower()
    )


def test_extract_suspicious_javascript_safe():
    pdf_bytes = _read_matrix_fixture("suspicious_javascript.pdf")
    doc = extract_pdf_document(pdf_bytes)
    assert doc.page_count == 1
    assert "Security audit test fixture" in doc.text


def test_extract_digital_pdf_success():
    fixture_path = os.path.join(FIXTURES_DIR, "simple_mcq.pdf")
    with open(fixture_path, "rb") as f:
        pdf_bytes = f.read()

    doc = extract_pdf_document(pdf_bytes)
    assert doc.source_type == DocumentSourceType.PDF_TEXT
    assert doc.page_count >= 1
    assert "General Science Quiz" in doc.text
    assert "chemical symbol for Water" in doc.text
    assert "Red Planet" in doc.text


def test_extract_sections_pdf():
    fixture_path = os.path.join(FIXTURES_DIR, "sections.pdf")
    with open(fixture_path, "rb") as f:
        pdf_bytes = f.read()

    doc = extract_pdf_document(pdf_bytes)
    assert doc.source_type == DocumentSourceType.PDF_TEXT
    assert "Section A" in doc.text
    assert "Section B" in doc.text


def test_extract_empty_pdf_bytes():
    with pytest.raises(DocumentExtractionError):
        extract_pdf_document(b"")


def test_extract_corrupt_pdf():
    with pytest.raises(DocumentExtractionError) as exc_info:
        extract_pdf_document(
            b"%PDF-1.4\nthis is definitely a corrupt stream without trailer"
        )
    assert (
        "corrupt" in str(exc_info.value).lower() or "pdf" in str(exc_info.value).lower()
    )


def test_extract_scanned_pdf_detection():
    fixture_path = os.path.join(FIXTURES_DIR, "scanned_sample.pdf")
    with open(fixture_path, "rb") as f:
        pdf_bytes = f.read()

    doc = extract_pdf_document(pdf_bytes)
    # Since this fixture has no digital text, it is classified as PDF_SCANNED
    assert doc.source_type == DocumentSourceType.PDF_SCANNED


def test_extract_scanned_pdf_content_raises_safe_error():
    from unittest.mock import patch

    from app.ai.extraction.document import ExtractedDocument

    blank_doc = ExtractedDocument(
        text="",
        source_type=DocumentSourceType.PDF_SCANNED,
        page_count=1,
    )
    with patch(
        "app.ai.extraction.question_paper.extract_pdf_document", return_value=blank_doc
    ):
        with pytest.raises(DocumentExtractionError) as exc_info:
            extract_document_content(
                b"%PDF-1.4\nblank", file_type="application/pdf", filename="scanned.pdf"
            )
        assert "scanned" in str(exc_info.value).lower()


def test_extract_valid_image():
    fixture_path = os.path.join(FIXTURES_DIR, "sample_paper.png")
    with open(fixture_path, "rb") as f:
        img_bytes = f.read()

    doc = extract_image_document(img_bytes, filename="sample_paper.png")
    assert doc.source_type == DocumentSourceType.IMAGE
    assert doc.metadata.get("width") == 400
    assert doc.metadata.get("height") == 300


def test_extract_corrupt_image():
    with pytest.raises(DocumentExtractionError) as exc_info:
        extract_image_document(
            b"\x89PNG\r\n\x1a\ncorruptimagedata", filename="corrupt.png"
        )
    assert "corrupt" in str(exc_info.value).lower()
