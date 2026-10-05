"""Structured answer key extraction using Cohere structured outputs."""

import json
import logging
from typing import Any

from app.ai.clients.cohere_client import CohereClient
from app.ai.extraction.document import (
    DocumentExtractionError,
    ExtractedDocument,
)
from app.ai.prompts.answer_key import (
    SYSTEM_ANSWER_KEY_EXTRACTION_PROMPT,
    build_answer_key_user_prompt,
)
from app.ai.schemas.answer_key import (
    ExtractedAnswer,
    ExtractedAnswerKey,
)

logger = logging.getLogger(__name__)


def merge_and_deduplicate_answers(
    answers_list: list[ExtractedAnswer],
) -> list[ExtractedAnswer]:
    """Merges extracted answers across chunk boundaries deterministically."""
    seen_refs: set[str] = set()
    deduped: list[ExtractedAnswer] = []

    for ans in answers_list:
        norm_ref = (ans.question_reference or "").strip().lower()
        if not norm_ref:
            deduped.append(ans)
            continue

        if norm_ref in seen_refs:
            logger.info("Deduplicating answer key item with ref: '%s'", ans.question_reference)
            continue

        seen_refs.add(norm_ref)
        deduped.append(ans)

    return deduped


async def extract_answer_key_from_document(
    doc: ExtractedDocument,
    cohere_client: CohereClient | None = None,
    exam_title: str | None = None,
) -> tuple[ExtractedAnswerKey, dict[str, Any]]:
    """Extracts structured answer key and rubrics from an ExtractedDocument using Cohere JSON Schema output.

    Handles windowing/chunking for multi-page documents and deterministic merging.
    """
    client = cohere_client or CohereClient()
    schema = ExtractedAnswerKey.model_json_schema()

    pages = doc.pages
    if len(pages) > 10:
        chunk_size = 5
        page_chunks: list[list[Any]] = [
            pages[i : i + chunk_size] for i in range(0, len(pages), chunk_size)
        ]
        logger.info(
            "Answer key document has %d pages, processing in %d chunks of %d pages",
            len(pages),
            len(page_chunks),
            chunk_size,
        )
    else:
        page_chunks = [pages]

    all_extracted_answers: list[ExtractedAnswer] = []
    doc_title: str | None = None
    exam_ref: str | None = exam_title
    total_marks: float | None = None
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
            "exam_title": exam_title,
        }

        messages = [
            {"role": "system", "content": SYSTEM_ANSWER_KEY_EXTRACTION_PROMPT},
            {
                "role": "user",
                "content": build_answer_key_user_prompt(chunk_text, metadata),
            },
        ]

        raw_json, metrics = await client.extract_structured_json(
            messages=messages,
            schema=schema,
        )

        total_metrics["retries"] += metrics.get("retries", 0)
        total_metrics["model"] = metrics.get("model")

        try:
            parsed_dict = json.loads(raw_json)
        except json.JSONDecodeError as e:
            logger.error("Cohere returned invalid JSON for answer key: %s", e)
            raise DocumentExtractionError(
                f"Failed to parse AI answer key response into valid JSON: {str(e)}"
            ) from e

        chunk_key = ExtractedAnswerKey.model_validate(parsed_dict)

        if chunk_idx == 1:
            doc_title = chunk_key.title
            if chunk_key.exam_reference:
                exam_ref = chunk_key.exam_reference
            total_marks = chunk_key.total_marks

        warnings.extend(chunk_key.warnings)
        all_extracted_answers.extend(chunk_key.answers)

    deduped_answers = merge_and_deduplicate_answers(all_extracted_answers)

    final_key = ExtractedAnswerKey(
        title=doc_title,
        exam_reference=exam_ref,
        answers=deduped_answers,
        total_marks=total_marks,
        warnings=list(set(warnings)),
    )

    total_metrics["answer_count"] = len(deduped_answers)
    return final_key, total_metrics
