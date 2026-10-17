"""Deterministic digital PDF text extraction using pdfplumber."""

import io
import logging

import pdfplumber

from app.ai.extraction.document import (
    DocumentExtractionError,
    DocumentSourceType,
    ExtractedDocument,
    PageContent,
)

logger = logging.getLogger(__name__)


MAX_PDF_PAGES = 50


def extract_pdf_document(file_bytes: bytes) -> ExtractedDocument:
    """Extracts text and page boundaries from a PDF file deterministically.

    Supports both digital PDFs and scanned PDFs using OCR page-level fallback.
    """
    if not file_bytes:
        raise DocumentExtractionError("PDF file content is empty")

    pages: list[PageContent] = []
    total_text_parts: list[str] = []
    scanned_pages_count = 0

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if len(pdf.pages) == 0:
                raise DocumentExtractionError("PDF contains no pages")
            if len(pdf.pages) > MAX_PDF_PAGES:
                raise DocumentExtractionError(
                    f"PDF exceeds the maximum supported limit of {MAX_PDF_PAGES} pages."
                )

            for idx, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text(layout=True) or ""
                # Also try standard extraction if layout produces empty
                if not page_text.strip():
                    page_text = page.extract_text() or ""

                page_text_clean = page_text.strip()
                has_images = len(page.images) > 0 if hasattr(page, "images") else False

                # If digital text is minimal (< 30 chars), attempt OCR on the page
                if len(page_text_clean) < 30:
                    try:
                        import pytesseract

                        img_obj = page.to_image(resolution=150)
                        ocr_text = (
                            pytesseract.image_to_string(img_obj.original) or ""
                        ).strip()
                        if len(ocr_text) > len(page_text_clean):
                            page_text_clean = ocr_text
                            has_images = True
                            scanned_pages_count += 1
                    except Exception as ocr_err:
                        logger.warning(
                            "OCR processing on PDF page %d was skipped or failed: %s",
                            idx,
                            ocr_err,
                        )

                pages.append(
                    PageContent(
                        page_number=idx,
                        text=page_text_clean,
                        char_count=len(page_text_clean),
                        has_images=has_images,
                    )
                )
                if page_text_clean:
                    total_text_parts.append(f"--- Page {idx} ---\n{page_text_clean}\n")

    except DocumentExtractionError:
        raise
    except Exception as e:
        logger.error("Failed to parse PDF document: %s", e)
        raise DocumentExtractionError(f"Corrupt or unreadable PDF: {str(e)}") from e

    full_text = "\n".join(total_text_parts).strip()
    total_chars = sum(p.char_count for p in pages)
    page_count = len(pages)
    avg_chars_per_page = total_chars / max(page_count, 1)

    # Classify source type based on text content density and OCR usage
    if scanned_pages_count > 0 and scanned_pages_count >= (page_count / 2):
        source_type = DocumentSourceType.PDF_SCANNED
    elif total_chars >= 50 and avg_chars_per_page >= 20:
        source_type = DocumentSourceType.PDF_TEXT
    else:
        source_type = DocumentSourceType.PDF_SCANNED

    return ExtractedDocument(
        source_type=source_type,
        text=full_text,
        pages=pages,
        page_count=page_count,
        metadata={
            "total_chars": total_chars,
            "avg_chars_per_page": round(avg_chars_per_page, 1),
            "scanned_pages_count": scanned_pages_count,
        },
    )
