"""Document extraction models and file validation utilities."""

import os
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DocumentSourceType(StrEnum):
    PDF_TEXT = "PDF_TEXT"
    PDF_SCANNED = "PDF_SCANNED"
    IMAGE = "IMAGE"
    UNKNOWN = "UNKNOWN"


@dataclass
class PageContent:
    page_number: int
    text: str
    char_count: int
    has_images: bool = False


@dataclass
class ExtractedDocument:
    source_type: DocumentSourceType
    text: str
    pages: list[PageContent] = field(default_factory=list)
    page_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentValidationError(Exception):
    """Raised when an uploaded document fails security or format validation."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class DocumentExtractionError(Exception):
    """Raised when document content cannot be parsed or extracted."""

    pass


# Magic bytes definitions for supported file formats
MAGIC_SIGNATURES: dict[str, list[bytes]] = {
    "application/pdf": [b"%PDF-"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/jpeg": [b"\xff\xd8\xff"],
}

MIME_EXTENSIONS: dict[str, set[str]] = {
    "application/pdf": {".pdf"},
    "image/png": {".png"},
    "image/jpeg": {".jpg", ".jpeg"},
}

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


def validate_uploaded_file(
    filename: str,
    declared_content_type: str,
    file_bytes: bytes,
    max_mb: int = 15,
) -> tuple[str, str]:
    """Strictly validates uploaded question paper files against security and format rules.

    Checks:
    1. Non-empty file
    2. Size limit
    3. Filename sanitization (no path traversal, valid extension)
    4. Magic bytes / signature check matching declared content type

    Returns:
        Tuple of (clean_extension, verified_mime_type)
    """
    if not file_bytes or len(file_bytes) == 0:
        raise DocumentValidationError("Uploaded file is empty", status_code=400)

    max_bytes = max_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise DocumentValidationError(
            f"File exceeds maximum allowed size of {max_mb} MB",
            status_code=413,
        )

    # Sanitize and extract extension
    basename = os.path.basename(filename).strip()
    if not basename or "/" in filename or "\\" in filename:
        raise DocumentValidationError("Invalid file path or name", status_code=400)

    # Disallow dangerous double extensions, e.g. "exam.php.pdf"
    parts = basename.split(".")
    if len(parts) > 2:
        # Check intermediate extensions
        for part in parts[1:-1]:
            if part.lower() in ("php", "exe", "sh", "py", "js", "html", "bat", "cmd", "jsp"):
                raise DocumentValidationError(
                    "Suspicious multiple extensions detected", status_code=400
                )

    ext = f".{parts[-1].lower()}" if len(parts) > 1 else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise DocumentValidationError(
            f"Unsupported file extension: '{ext}'. Allowed extensions: PDF, PNG, JPG, JPEG",
            status_code=415,
        )

    # Verify declared MIME type
    norm_content_type = declared_content_type.lower().split(";")[0].strip()
    if norm_content_type not in MAGIC_SIGNATURES:
        raise DocumentValidationError(
            f"Unsupported MIME type: '{declared_content_type}'. Allowed types: application/pdf, image/png, image/jpeg",
            status_code=415,
        )

    # Ensure extension matches declared MIME type
    if ext not in MIME_EXTENSIONS.get(norm_content_type, set()):
        raise DocumentValidationError(
            f"File extension '{ext}' does not match declared content type '{declared_content_type}'",
            status_code=415,
        )

    # Magic byte verification
    valid_signatures = MAGIC_SIGNATURES[norm_content_type]
    signature_matches = any(file_bytes.startswith(sig) for sig in valid_signatures)
    if not signature_matches:
        raise DocumentValidationError(
            "File header signature (magic bytes) does not match the declared file type",
            status_code=415,
        )

    return ext, norm_content_type
