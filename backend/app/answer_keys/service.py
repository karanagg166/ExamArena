"""Service layer orchestrating Answer Key import processing, matching, and confirmation."""

import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import app.core.database as db
from app.ai.clients.cohere_client import (
    CohereAPIError,
    CohereClient,
    CohereClientError,
    CohereConfigurationError,
    CohereRateLimitError,
    CohereTimeoutError,
)
from app.ai.extraction import (
    DocumentExtractionError,
    DocumentSourceType,
    extract_document_content,
)
from app.ai.extraction.answer_key import extract_answer_key_from_document
from app.ai.matching.answer_key import match_extracted_answer_key
from app.ai.schemas.answer_key import (
    ExtractedAnswerKey,
    MatchedAnswer,
    MatchedAnswerKey,
    MatchStatus,
)
from app.answer_keys import crud
from app.answer_keys.schemas import (
    AnswerKeyImportConfirmResponse,
    AnswerKeyImportResponse,
)
from app.audit.actions import AuditAction, AuditResourceType
from app.audit.service import record_audit_event
from app.core.models import (
    AnswerKeyImport,
    AnswerKeyImportSourceType,
    AnswerKeyImportStatus,
    Exam,
    Question,
    QuestionOption,
    utc_now,
)
from app.storage.base import StorageReadError
from app.storage.service import get_storage_provider, resolve_storage_resource_type

logger = logging.getLogger(__name__)


def format_answer_key_response(record: AnswerKeyImport) -> AnswerKeyImportResponse:
    """Converts a database AnswerKeyImport entity to a clean API response."""
    answers: list[MatchedAnswer] = []
    title = None
    exam_reference = None
    warnings: list[str] = []
    matched_count = 0
    ambiguous_count = 0
    unmatched_count = 0
    total_answers = 0

    if record.validatedExtraction and isinstance(record.validatedExtraction, dict):
        try:
            matched_key = MatchedAnswerKey.model_validate(record.validatedExtraction)
            answers = matched_key.answers
            warnings = matched_key.warnings
            matched_count = matched_key.matched_count
            ambiguous_count = matched_key.ambiguous_count
            unmatched_count = matched_key.unmatched_count
            total_answers = matched_key.total_answers
        except Exception as e:
            logger.warning(
                "Failed to parse validatedExtraction in answer key import %s: %s",
                record.id,
                e,
            )

    if record.rawExtraction and isinstance(record.rawExtraction, dict):
        title = record.rawExtraction.get("title")
        exam_reference = record.rawExtraction.get("exam_reference")

    return AnswerKeyImportResponse(
        id=record.id,
        examId=record.examId,
        teacherId=record.teacherId,
        originalFileName=record.originalFileName,
        fileType=record.fileType,
        fileSize=record.fileSize,
        status=record.status,
        sourceType=record.sourceType,
        errorMessage=record.errorMessage,
        errorCategory=record.errorCategory,
        createdAt=record.createdAt,
        updatedAt=record.updatedAt,
        completedAt=record.completedAt,
        confirmedAt=record.confirmedAt,
        matchedCount=matched_count,
        ambiguousCount=ambiguous_count,
        unmatchedCount=unmatched_count,
        totalAnswers=total_answers,
        title=title,
        examReference=exam_reference,
        answers=answers if answers else None,
        warnings=warnings,
        storageProvider=record.storageProvider,
        storageUrl=record.storageUrl,
    )


async def process_answer_key_import(
    import_id: str,
    cohere_client: CohereClient | None = None,
) -> None:
    """Background task processing uploaded answer key, extracting structure, and matching against exam questions."""
    logger.info("Starting background processing for AnswerKeyImport %s", import_id)
    record = await crud.get_answer_key_import_by_id(import_id)
    if not record:
        logger.error("AnswerKeyImport record %s not found for processing", import_id)
        return

    # Check status
    if record.status in (
        AnswerKeyImportStatus.COMPLETED,
        AnswerKeyImportStatus.CANCELLED,
    ):
        logger.info(
            "AnswerKeyImport %s is in terminal state '%s', aborting",
            import_id,
            record.status,
        )
        return

    await crud.update_answer_key_import_processing_start(import_id)

    try:
        # 1. Fetch file from storage
        storage = get_storage_provider()
        file_key = record.storageKey or record.filePath
        resource_type = resolve_storage_resource_type(
            record.storageResourceType, record.fileType
        )
        file_bytes = await storage.get_file(file_key, resource_type=resource_type)

        # 2. Extract document text
        extracted_doc = extract_document_content(
            file_bytes,
            record.fileType,
            filename=record.originalFileName,
        )

        source_type_map = {
            DocumentSourceType.PDF_TEXT: AnswerKeyImportSourceType.PDF_TEXT,
            DocumentSourceType.PDF_SCANNED: AnswerKeyImportSourceType.PDF_SCANNED,
            DocumentSourceType.IMAGE: AnswerKeyImportSourceType.IMAGE,
            DocumentSourceType.UNKNOWN: AnswerKeyImportSourceType.UNKNOWN,
        }
        db_source_type = source_type_map.get(
            extracted_doc.source_type, AnswerKeyImportSourceType.UNKNOWN
        )

        # 3. Fetch exam and questions to match against
        async with db.get_session() as session:
            exam_stmt = (
                select(Exam)
                .where(Exam.id == record.examId)
                .options(selectinload(Exam.questions).selectinload(Question.options))
            )
            exam = (await session.execute(exam_stmt)).scalar_one_or_none()
            if not exam:
                raise DocumentExtractionError(
                    f"Exam {record.examId} not found for answer key matching."
                )
            exam_questions = list(exam.questions or [])
            exam_title = exam.title

        # 4. Cohere structured answer key extraction
        extracted_key, metrics = await extract_answer_key_from_document(
            extracted_doc,
            cohere_client=cohere_client,
            exam_title=exam_title,
        )

        if not extracted_key.answers:
            raise DocumentExtractionError(
                "No answers could be detected or extracted from the uploaded document."
            )

        # 5. Deterministic matching
        matched_key = match_extracted_answer_key(
            extracted=extracted_key,
            exam_questions=exam_questions,
            exam_id=record.examId,
            import_id=import_id,
        )

        # 6. Save draft in database
        raw_dict = extracted_key.model_dump()
        val_dict = matched_key.model_dump()
        await crud.update_answer_key_import_success(
            import_id=import_id,
            source_type=db_source_type,
            extracted_text=extracted_doc.text,
            raw_extraction=raw_dict,
            validated_extraction=val_dict,
        )
        logger.info(
            "AnswerKeyImport %s successfully extracted %d answers (%d matched, %d ambiguous, %d unmatched)",
            import_id,
            matched_key.total_answers,
            matched_key.matched_count,
            matched_key.ambiguous_count,
            matched_key.unmatched_count,
        )

    except StorageReadError as e:
        logger.warning("Storage read failed for answer key %s", import_id)
        await crud.update_answer_key_import_failure(
            import_id,
            error_category="STORAGE_READ",
            error_message=str(e),
        )

    except DocumentExtractionError as e:
        logger.warning("Document extraction failed for answer key %s: %s", import_id, e)
        await crud.update_answer_key_import_failure(
            import_id,
            error_category="DOCUMENT_PARSING",
            error_message=str(e),
        )

    except CohereConfigurationError as e:
        logger.error("Cohere configuration error for answer key %s: %s", import_id, e)
        await crud.update_answer_key_import_failure(
            import_id,
            error_category="CONFIGURATION",
            error_message="AI extraction service is not configured. Please contact administrator.",
        )

    except CohereRateLimitError as e:
        logger.warning("Cohere rate limit for answer key %s: %s", import_id, e)
        await crud.update_answer_key_import_failure(
            import_id,
            error_category="RATE_LIMIT",
            error_message="AI service rate limit exceeded. Please try importing again shortly.",
        )

    except CohereTimeoutError as e:
        logger.warning("Cohere timeout for answer key %s: %s", import_id, e)
        await crud.update_answer_key_import_failure(
            import_id,
            error_category="TIMEOUT",
            error_message="AI service timed out while analyzing the answer key. Please try again.",
        )

    except CohereAPIError as e:
        logger.error("Cohere API error for answer key %s: %s", import_id, e)
        await crud.update_answer_key_import_failure(
            import_id,
            error_category="PROVIDER_ERROR",
            error_message="AI service encountered an issue processing the answer key. Please try again.",
        )

    except Exception as e:
        logger.exception("Unexpected error processing answer key %s: %s", import_id, e)
        await crud.update_answer_key_import_failure(
            import_id,
            error_category="INTERNAL_ERROR",
            error_message=f"An unexpected internal error occurred: {str(e)}",
        )


async def confirm_answer_key_import(
    import_id: str,
    user_id: str,
    overwrite_existing: bool = False,
    edited_answers: list[MatchedAnswer] | None = None,
) -> AnswerKeyImportConfirmResponse:
    """Applies confirmed answer key mappings to exam questions transactionally."""
    record = await crud.get_answer_key_import_by_id(import_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer key import job not found",
        )

    if record.status == AnswerKeyImportStatus.COMPLETED:
        return AnswerKeyImportConfirmResponse(
            id=record.id,
            examId=record.examId,
            status=record.status,
            updatedQuestionsCount=0,
            confirmedAt=record.confirmedAt or utc_now(),
        )

    if record.status != AnswerKeyImportStatus.NEEDS_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot confirm answer key import in '{record.status}' status. Must be in NEEDS_REVIEW.",
        )

    # Determine answers list
    answers_to_apply: list[MatchedAnswer] = []
    if edited_answers is not None:
        answers_to_apply = edited_answers
    elif record.validatedExtraction and isinstance(record.validatedExtraction, dict):
        try:
            matched_key = MatchedAnswerKey.model_validate(record.validatedExtraction)
            answers_to_apply = matched_key.answers
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid validated extraction data: {e}",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No validated extraction data available to confirm.",
        )

    matched_items = [
        a
        for a in answers_to_apply
        if a.status == MatchStatus.MATCHED and a.matched_question_id
    ]

    if not matched_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No matched questions to apply. Please map at least one answer before confirming.",
        )

    updated_count = 0
    now = utc_now()

    async with db.get_session() as session:
        async with session.begin():
            # Check exam
            exam_stmt = select(Exam).where(Exam.id == record.examId)
            exam = (await session.execute(exam_stmt)).scalar_one_or_none()
            if not exam:
                raise HTTPException(status_code=404, detail="Associated exam not found")

            # Load target questions
            target_q_ids = [
                a.matched_question_id for a in matched_items if a.matched_question_id
            ]
            q_stmt = (
                select(Question)
                .where(Question.id.in_(target_q_ids), Question.examId == record.examId)
                .options(selectinload(Question.options))
            )
            questions_by_id = {
                q.id: q for q in (await session.execute(q_stmt)).scalars().all()
            }

            for item in matched_items:
                if (
                    not item.matched_question_id
                    or item.matched_question_id not in questions_by_id
                ):
                    continue

                q = questions_by_id[item.matched_question_id]
                changed = False

                # 1. Update objective options
                if q.questionType in (
                    "MULTIPLE_CHOICE",
                    "TRUE_FALSE",
                    "MULTIPLE_SELECT",
                ):
                    correct_ids = set(item.matched_option_ids)
                    valid_ids = {opt.id for opt in q.options}
                    if (
                        not correct_ids
                        or not correct_ids <= valid_ids
                        or (
                            q.questionType in ("MULTIPLE_CHOICE", "TRUE_FALSE")
                            and len(correct_ids) != 1
                        )
                    ):
                        raise HTTPException(
                            status_code=400,
                            detail="Objective answer must contain valid options and the required selection count.",
                        )
                    already_has_correct = any(opt.isCorrect for opt in q.options)
                    if not already_has_correct or overwrite_existing:
                        for opt in q.options:
                            should_be_correct = opt.id in correct_ids
                            if opt.isCorrect != should_be_correct:
                                opt.isCorrect = should_be_correct
                                changed = True

                # 2. Update reference answer for subjective questions
                if q.questionType in ("SHORT_ANSWER", "ESSAY"):
                    if item.reference_answer:
                        if not q.referenceAnswer or overwrite_existing:
                            if q.referenceAnswer != item.reference_answer:
                                q.referenceAnswer = item.reference_answer
                                changed = True

                # 3. Update grading rubric
                if item.rubric:
                    rubric_dicts = [
                        (r.model_dump() if hasattr(r, "model_dump") else r)
                        for r in item.rubric
                    ]
                    if not q.gradingRubric or overwrite_existing:
                        q.gradingRubric = rubric_dicts
                        changed = True

                # 4. Update explanation
                if item.explanation:
                    if not q.explanation or overwrite_existing:
                        if q.explanation != item.explanation:
                            q.explanation = item.explanation
                            changed = True

                if changed:
                    q.updatedAt = now
                    updated_count += 1

            # Update import record in same transaction
            record_stmt = select(AnswerKeyImport).where(AnswerKeyImport.id == record.id)
            attached_record = (await session.execute(record_stmt)).scalar_one_or_none()
            if attached_record:
                attached_record.status = AnswerKeyImportStatus.COMPLETED
                attached_record.confirmedAt = now
                attached_record.updatedAt = now

    # Audit event
    await record_audit_event(
        action=AuditAction.QUESTION_UPDATED,
        resource_type=AuditResourceType.EXAM,
        resource_id=record.examId,
        metadata={
            "importId": record.id,
            "updatedQuestionsCount": updated_count,
            "overwriteExisting": overwrite_existing,
        },
    )

    logger.info(
        "Successfully confirmed AnswerKeyImport %s: updated %d questions",
        record.id,
        updated_count,
    )

    return AnswerKeyImportConfirmResponse(
        id=record.id,
        examId=record.examId,
        status=AnswerKeyImportStatus.COMPLETED,
        updatedQuestionsCount=updated_count,
        confirmedAt=now,
    )
