"""Unit tests for question paper upload validation (MIME, magic bytes, path traversal, size limits)."""

import pytest

from app.ai.extraction.document import (
    DocumentValidationError,
    validate_uploaded_file,
)


def test_validate_valid_pdf():
    valid_pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    ext, mime = validate_uploaded_file(
        filename="midterm.pdf",
        declared_content_type="application/pdf",
        file_bytes=valid_pdf_content,
        max_mb=15,
    )
    assert ext == ".pdf"
    assert mime == "application/pdf"


def test_validate_valid_png():
    valid_png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    ext, mime = validate_uploaded_file(
        filename="diagram.png",
        declared_content_type="image/png",
        file_bytes=valid_png_content,
        max_mb=15,
    )
    assert ext == ".png"
    assert mime == "image/png"


def test_validate_valid_jpeg():
    valid_jpeg_content = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    ext, mime = validate_uploaded_file(
        filename="photo.jpg",
        declared_content_type="image/jpeg",
        file_bytes=valid_jpeg_content,
        max_mb=15,
    )
    assert ext == ".jpg"
    assert mime == "image/jpeg"


def test_validate_empty_file():
    with pytest.raises(DocumentValidationError) as exc_info:
        validate_uploaded_file(
            filename="empty.pdf",
            declared_content_type="application/pdf",
            file_bytes=b"",
        )
    assert exc_info.value.status_code == 400
    assert "empty" in str(exc_info.value).lower()


def test_validate_oversized_file():
    one_mb_bytes = b"x" * (1024 * 1024 + 1)
    with pytest.raises(DocumentValidationError) as exc_info:
        validate_uploaded_file(
            filename="large.pdf",
            declared_content_type="application/pdf",
            file_bytes=one_mb_bytes,
            max_mb=1,
        )
    assert exc_info.value.status_code == 413
    assert "exceeds maximum" in str(exc_info.value).lower()


def test_validate_path_traversal_filename():
    valid_pdf_content = b"%PDF-1.4\n%%EOF"
    with pytest.raises(DocumentValidationError) as exc_info:
        validate_uploaded_file(
            filename="../../etc/passwd.pdf",
            declared_content_type="application/pdf",
            file_bytes=valid_pdf_content,
        )
    assert exc_info.value.status_code == 400


def test_validate_dangerous_double_extension():
    valid_pdf_content = b"%PDF-1.4\n%%EOF"
    with pytest.raises(DocumentValidationError) as exc_info:
        validate_uploaded_file(
            filename="exam.php.pdf",
            declared_content_type="application/pdf",
            file_bytes=valid_pdf_content,
        )
    assert exc_info.value.status_code == 400
    assert "multiple extensions" in str(exc_info.value).lower()


def test_validate_fake_pdf_extension_with_wrong_magic_bytes():
    fake_pdf_content = b"This is not a pdf file but plain text"
    with pytest.raises(DocumentValidationError) as exc_info:
        validate_uploaded_file(
            filename="fake.pdf",
            declared_content_type="application/pdf",
            file_bytes=fake_pdf_content,
        )
    assert exc_info.value.status_code == 415
    assert "signature" in str(exc_info.value).lower()


def test_validate_fake_image_extension_with_wrong_magic_bytes():
    fake_png_content = b"%PDF-1.4 but named png"
    with pytest.raises(DocumentValidationError) as exc_info:
        validate_uploaded_file(
            filename="fake.png",
            declared_content_type="image/png",
            file_bytes=fake_png_content,
        )
    assert exc_info.value.status_code == 415
    assert "signature" in str(exc_info.value).lower()


def test_validate_unsupported_mime_type():
    with pytest.raises(DocumentValidationError) as exc_info:
        validate_uploaded_file(
            filename="doc.docx",
            declared_content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            file_bytes=b"PK\x03\x04",
        )
    assert exc_info.value.status_code == 415
