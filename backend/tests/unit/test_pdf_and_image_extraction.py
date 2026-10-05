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

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "question_papers")


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
        extract_pdf_document(b"%PDF-1.4\nthis is definitely a corrupt stream without trailer")
    assert "corrupt" in str(exc_info.value).lower() or "pdf" in str(exc_info.value).lower()


def test_extract_scanned_pdf_detection():
    fixture_path = os.path.join(FIXTURES_DIR, "scanned_sample.pdf")
    with open(fixture_path, "rb") as f:
        pdf_bytes = f.read()

    doc = extract_pdf_document(pdf_bytes)
    # Since this fixture has no digital text, it is classified as PDF_SCANNED
    assert doc.source_type == DocumentSourceType.PDF_SCANNED


def test_extract_scanned_pdf_content_raises_safe_error():
    fixture_path = os.path.join(FIXTURES_DIR, "scanned_sample.pdf")
    with open(fixture_path, "rb") as f:
        pdf_bytes = f.read()

    with pytest.raises(DocumentExtractionError) as exc_info:
        extract_document_content(pdf_bytes, file_type="application/pdf", filename="scanned.pdf")
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
        extract_image_document(b"\x89PNG\r\n\x1a\ncorruptimagedata", filename="corrupt.png")
    assert "corrupt" in str(exc_info.value).lower()
