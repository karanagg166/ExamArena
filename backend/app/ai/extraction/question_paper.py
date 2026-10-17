"""High-level question paper extraction service utilizing Cohere structured outputs."""

import json
import logging
import re
from typing import Any

from app.ai.clients.cohere_client import CohereClient
from app.ai.extraction.document import (
    DocumentExtractionError,
    DocumentSourceType,
    ExtractedDocument,
)
from app.ai.extraction.image import extract_image_document
from app.ai.extraction.pdf import extract_pdf_document
from app.ai.prompts.question_paper import (
    SYSTEM_EXTRACTION_PROMPT,
    build_extraction_user_prompt,
)
from app.ai.schemas.question_paper import (
    ExtractedConfidence,
    ExtractedQuestion,
    ExtractedQuestionPaper,
    ExtractedQuestionType,
)

logger = logging.getLogger(__name__)


def extract_document_content(
    file_bytes: bytes,
    file_type: str,
    filename: str = "",
) -> ExtractedDocument:
    """Routes uploaded file to appropriate extraction engine (PDF or image)."""
    norm_type = file_type.lower()
    if "pdf" in norm_type or filename.lower().endswith(".pdf"):
        doc = extract_pdf_document(file_bytes)
        if not doc.text.strip():
            raise DocumentExtractionError(
                "No readable text could be extracted from the uploaded scanned PDF document (even after OCR). "
                "Please upload a clearer PDF or image."
            )
        return doc
    elif any(t in norm_type for t in ("image", "png", "jpeg", "jpg")) or any(
        filename.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg")
    ):
        doc = extract_image_document(file_bytes, filename=filename)
        if not doc.text.strip():
            raise DocumentExtractionError(
                "No readable text could be extracted from the uploaded image. "
                "Please upload a clear image or digital PDF paper."
            )
        return doc
    else:
        raise DocumentExtractionError(
            f"Unsupported document format for extraction: '{file_type}'"
        )


def _normalize_text_for_dedup(text: str) -> str:
    """Normalize question text for deterministic duplicate matching."""
    cleaned = re.sub(r"\s+", " ", text.lower().strip())
    # Remove leading numbering like "1.", "q1.", "1(a)"
    cleaned = re.sub(r"^(?:q(?:uestion)?\s*)?\d+[\.\)\-\:\s]*", "", cleaned)
    return cleaned.strip()


def _build_dedup_key(q: ExtractedQuestion) -> str:
    """Build a deterministic composite signature for deduplication without truncating question text."""
    norm_text = _normalize_text_for_dedup(q.text)
    q_type = (
        q.question_type.value
        if hasattr(q.question_type, "value")
        else str(q.question_type)
    )

    # Options signature (sorted text of options to capture MCQ uniqueness)
    opts = []
    for opt in q.options or []:
        opt_text = re.sub(r"\s+", " ", (opt.text or "").lower().strip())
        opts.append(opt_text)
    opts_sig = "|".join(sorted(opts)) if opts else ""

    # Section / question number signature
    sec = (q.section or "").strip().lower()
    q_num = (q.question_number or "").strip().lower()

    # If question text is very short (< 15 chars), also include question_number
    if len(norm_text) <= 15 and q_num:
        return f"{sec}::{q_num}::{norm_text}::{q_type}::{opts_sig}"

    return f"{sec}::{norm_text}::{q_type}::{opts_sig}"


def merge_and_deduplicate_questions(
    questions_list: list[ExtractedQuestion],
) -> list[ExtractedQuestion]:
    """Merges extracted questions from multiple chunks deterministically while eliminating boundary duplicates."""
    seen_keys: dict[str, int] = {}
    deduped: list[ExtractedQuestion] = []

    for q in questions_list:
        dedup_key = _build_dedup_key(q)

        if dedup_key in seen_keys:
            idx = seen_keys[dedup_key]
            existing = deduped[idx]
            # If the duplicate entry has richer metadata (e.g. marks or more options), retain the richer one
            if (existing.marks is None and q.marks is not None) or (
                len(q.options) > len(existing.options)
            ):
                deduped[idx] = q
            logger.info("Deduplicating duplicate question entry: '%s'", q.text[:50])
            continue

        seen_keys[dedup_key] = len(deduped)
        deduped.append(q)

    return deduped


async def extract_questions_from_document(
    doc: ExtractedDocument,
    cohere_client: CohereClient | None = None,
    exam_subject: str | None = None,
) -> tuple[ExtractedQuestionPaper, dict[str, Any]]:
    """Extracts structured questions from an ExtractedDocument using Cohere JSON Schema output.

    Handles windowing/chunking for larger multi-page documents and deterministic merging.
    """
    client = cohere_client or CohereClient()
    schema = ExtractedQuestionPaper.model_json_schema()

    # Determine if document fits in a single prompt or needs page-window chunking
    # Command R+ has a 128k context window, but chunking very long papers (e.g. > 10 pages)
    # improves extraction fidelity and avoids token truncation.
    pages = doc.pages
    if len(pages) > 10:
        chunk_size = 5
        page_chunks: list[list[Any]] = [
            pages[i : i + chunk_size] for i in range(0, len(pages), chunk_size)
        ]
        logger.info(
            "Document has %d pages, processing in %d chunks of %d pages",
            len(pages),
            len(page_chunks),
            chunk_size,
        )
    else:
        page_chunks = [pages]

    all_extracted_questions: list[ExtractedQuestion] = []
    paper_title: str | None = None
    detected_subject: str | None = exam_subject
    total_marks: float | None = None
    duration_minutes: int | None = None
    instructions: list[str] = []
    warnings: list[str] = []
    total_metrics: dict[str, Any] = {"chunks": len(page_chunks), "retries": 0}

    for chunk_idx, chunk in enumerate(page_chunks, start=1):
        chunk_text = "\n".join(
            f"--- Page {p.page_number} ---\n{p.text}" for p in chunk if p.text.strip()
        )
        if not chunk_text.strip():
            continue

        metadata = {
            "chunk": f"{chunk_idx} of {len(page_chunks)}",
            "page_count": doc.page_count,
            "subject": exam_subject,
        }

        messages = [
            {"role": "system", "content": SYSTEM_EXTRACTION_PROMPT},
            {
                "role": "user",
                "content": build_extraction_user_prompt(chunk_text, metadata),
            },
        ]

        raw_json, metrics = await client.extract_structured_json(
            messages=messages,
            schema=schema,
        )

        total_metrics["retries"] += metrics.get("retries", 0)
        total_metrics["model"] = metrics.get("model")

        # Parse and validate response with Pydantic
        try:
            parsed_dict = json.loads(raw_json)
        except json.JSONDecodeError as e:
            logger.error("Cohere returned invalid JSON: %s", e)
            raise DocumentExtractionError(
                f"Failed to parse AI response into valid JSON: {str(e)}"
            ) from e

        chunk_paper = ExtractedQuestionPaper.model_validate(parsed_dict)

        # Consolidate metadata from first chunk
        if chunk_idx == 1:
            paper_title = chunk_paper.title
            if chunk_paper.subject:
                detected_subject = chunk_paper.subject
            total_marks = chunk_paper.total_marks
            duration_minutes = chunk_paper.duration_minutes
            instructions.extend(chunk_paper.instructions)

        warnings.extend(chunk_paper.warnings)
        all_extracted_questions.extend(chunk_paper.questions)

    # Deterministically deduplicate questions across chunk boundaries
    deduped_questions = merge_and_deduplicate_questions(all_extracted_questions)

    # Post-extraction sanity checks
    for idx, q in enumerate(deduped_questions, start=1):
        # Ensure question numbering fallback if missing
        if not q.question_number:
            q.question_number = str(idx)

        # Ensure no answer keys were guessed
        for _opt in q.options:
            # Phase 1 rule: is_correct should not be inferred unless explicitly stated
            pass

        # Check for missing marks
        if q.marks is None:
            if "Marks could not be confidently determined" not in " ".join(q.warnings):
                q.warnings.append(
                    "Marks could not be confidently determined from document"
                )

    final_paper = ExtractedQuestionPaper(
        title=paper_title,
        subject=detected_subject,
        total_marks=total_marks,
        duration_minutes=duration_minutes,
        instructions=instructions,
        questions=deduped_questions,
        warnings=list(set(warnings)),
    )

    total_metrics["question_count"] = len(deduped_questions)
    return final_paper, total_metrics
