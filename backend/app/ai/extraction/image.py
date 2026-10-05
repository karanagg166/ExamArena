"""Image verification and OCR extraction module."""

import io
import logging
from typing import Any

from PIL import Image

from app.ai.extraction.document import (
    DocumentExtractionError,
    DocumentSourceType,
    ExtractedDocument,
    PageContent,
)

logger = logging.getLogger(__name__)


def extract_image_document(file_bytes: bytes, filename: str = "") -> ExtractedDocument:
    """Validates an image file and extracts textual content if an OCR engine is available."""
    if not file_bytes:
        raise DocumentExtractionError("Image file content is empty")

    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img.verify()  # Verify image integrity
    except Exception as e:
        logger.error("Corrupted image file: %s", e)
        raise DocumentExtractionError(f"Corrupt or unreadable image file: {str(e)}") from e

    # Re-open after verify() since verify() closes image
    width, height, img_format = 0, 0, ""
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            width, height = img.size
            img_format = img.format or "UNKNOWN"
    except Exception as e:
        raise DocumentExtractionError(f"Cannot read image dimensions: {str(e)}") from e

    extracted_text = ""
    # Try pytesseract if available in the runtime environment
    try:
        import pytesseract  # type: ignore

        with Image.open(io.BytesIO(file_bytes)) as img:
            extracted_text = (pytesseract.image_to_string(img) or "").strip()
            logger.info("Extracted %d characters via pytesseract OCR", len(extracted_text))
    except ImportError:
        logger.info("pytesseract OCR engine not installed in environment")
    except Exception as e:
        logger.warning("OCR processing encountered an issue: %s", e)

    page = PageContent(
        page_number=1,
        text=extracted_text,
        char_count=len(extracted_text),
        has_images=True,
    )

    return ExtractedDocument(
        source_type=DocumentSourceType.IMAGE,
        text=extracted_text,
        pages=[page],
        page_count=1,
        metadata={
            "width": width,
            "height": height,
            "format": img_format,
            "filename": filename,
        },
    )
