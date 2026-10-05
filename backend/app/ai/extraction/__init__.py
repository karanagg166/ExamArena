"""AI extraction package."""

from app.ai.extraction.document import (
    DocumentExtractionError,
    DocumentSourceType,
    DocumentValidationError,
    ExtractedDocument,
    PageContent,
    validate_uploaded_file,
)
from app.ai.extraction.image import extract_image_document
from app.ai.extraction.pdf import extract_pdf_document
from app.ai.extraction.question_paper import (
    extract_document_content,
    extract_questions_from_document,
    merge_and_deduplicate_questions,
)

__all__ = [
    "DocumentSourceType",
    "PageContent",
    "ExtractedDocument",
    "DocumentValidationError",
    "DocumentExtractionError",
    "validate_uploaded_file",
    "extract_pdf_document",
    "extract_image_document",
    "extract_document_content",
    "extract_questions_from_document",
    "merge_and_deduplicate_questions",
]
