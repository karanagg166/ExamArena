"""Service layer orchestrating Question Paper import processing and transactional confirmation."""

import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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
    extract_questions_from_document,
)
from app.ai.schemas.question_paper import (
    ExtractedQuestion,
    ExtractedQuestionPaper,
    ExtractedQuestionType,
)
from app.audit.actions import AuditAction, AuditResourceType
from app.audit.service import record_audit_event
from app.core.models import (
    Exam,
    ExamSection,
    Question,
    QuestionImport,
    QuestionImportSourceType,
    QuestionImportStatus,
    QuestionOption,
    QuestionType,
    utc_now,
)
from app.imports import crud
from app.imports.schemas import (
    QuestionImportConfirmResponse,
    QuestionImportResponse,
)
from app.storage.service import get_storage_provider
from app.users.schemas import UserResponse

logger = logging.getLogger(__name__)


def map_extracted_type_to_model(extracted_type: ExtractedQuestionType) -> QuestionType:
    """Map extracted question type to ExamArena QuestionType enum."""
    type_map = {
        ExtractedQuestionType.MULTIPLE_CHOICE: QuestionType.MULTIPLE_CHOICE,
        ExtractedQuestionType.MULTIPLE_SELECT: QuestionType.MULTIPLE_SELECT,
        ExtractedQuestionType.TRUE_FALSE: QuestionType.TRUE_FALSE,
        ExtractedQuestionType.SHORT_ANSWER: QuestionType.SHORT_ANSWER,
        ExtractedQuestionType.ESSAY: QuestionType.ESSAY,
    }
    if extracted_type not in type_map:
        raise ValueError(f"Cannot map unknown question type '{extracted_type}' to database model")
    return type_map[extracted_type]


def format_import_response(record: QuestionImport) -> QuestionImportResponse:
    """Converts a database QuestionImport entity to a clean API response."""
    questions: list[ExtractedQuestion] = []
    title = None
    subject = None
    warnings = []

    if record.validatedExtraction and isinstance(record.validatedExtraction, dict):
        try:
            paper = ExtractedQuestionPaper.model_validate(record.validatedExtraction)
            questions = paper.questions
            title = paper.title
            subject = paper.subject
            warnings = paper.warnings
        except Exception as e:
            logger.warning("Failed to parse validatedExtraction in record %s: %s", record.id, e)

    return QuestionImportResponse(
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
        questionCount=len(questions) if questions else 0,
        title=title,
        subject=subject,
        questions=questions if record.status != QuestionImportStatus.FAILED else None,
        warnings=warnings,
    )


async def process_question_import(
    import_id: str,
    cohere_client: CohereClient | None = None,
) -> None:
    """Asynchronous background worker job for parsing and extracting a question paper."""
    logger.info("Starting background processing for QuestionImport %s", import_id)
    record = await crud.get_question_import_by_id(import_id)
    if not record:
        logger.error("QuestionImport %s not found in database", import_id)
        return

    # Idempotency check: do not re-process if already in review or completed
    if record.status in (QuestionImportStatus.NEEDS_REVIEW, QuestionImportStatus.COMPLETED):
        logger.info(
            "QuestionImport %s is already in state %s. Skipping duplicate processing.",
            import_id,
            record.status,
        )
        return

    # Update status to PROCESSING
    await crud.update_question_import_processing_start(import_id)

    try:
        # 1. Fetch file from storage
        storage = get_storage_provider()
        file_bytes = await storage.get_file(record.filePath)

        # 2. Extract document structure and text
        extracted_doc = extract_document_content(
            file_bytes,
            record.fileType,
            filename=record.originalFileName,
        )

        source_type_map = {
            DocumentSourceType.PDF_TEXT: QuestionImportSourceType.PDF_TEXT,
            DocumentSourceType.PDF_SCANNED: QuestionImportSourceType.PDF_SCANNED,
            DocumentSourceType.IMAGE: QuestionImportSourceType.IMAGE,
            DocumentSourceType.UNKNOWN: QuestionImportSourceType.UNKNOWN,
        }
        db_source_type = source_type_map.get(
            extracted_doc.source_type, QuestionImportSourceType.UNKNOWN
        )

        # 3. Call Cohere structured extraction
        extracted_paper, metrics = await extract_questions_from_document(
            extracted_doc,
            cohere_client=cohere_client,
        )

        if not extracted_paper.questions:
            raise DocumentExtractionError("No questions could be detected or extracted from the uploaded document.")

        # 4. Save validated draft and transition to NEEDS_REVIEW
        paper_dict = extracted_paper.model_dump()
        await crud.update_question_import_success(
            import_id=import_id,
            source_type=db_source_type,
            extracted_text=extracted_doc.text,
            raw_extraction=paper_dict,
            validated_extraction=paper_dict,
        )
        logger.info(
            "QuestionImport %s successfully extracted %d questions",
            import_id,
            len(extracted_paper.questions),
        )

    except DocumentExtractionError as e:
        logger.warning("Document extraction failed for import %s: %s", import_id, e)
        await crud.update_question_import_failure(
            import_id,
            error_category="DOCUMENT_PARSING",
            error_message=str(e),
        )

    except CohereConfigurationError as e:
        logger.error("Cohere configuration error for import %s: %s", import_id, e)
        await crud.update_question_import_failure(
            import_id,
            error_category="CONFIGURATION",
            error_message="AI extraction service is not configured. Please contact administrator.",
        )

    except CohereRateLimitError as e:
        logger.warning("Cohere rate limit for import %s: %s", import_id, e)
        await crud.update_question_import_failure(
            import_id,
            error_category="RATE_LIMIT",
            error_message="AI service rate limit exceeded. Please try importing again shortly.",
        )

    except CohereTimeoutError as e:
        logger.warning("Cohere timeout for import %s: %s", import_id, e)
        await crud.update_question_import_failure(
            import_id,
            error_category="TIMEOUT",
            error_message="AI service timed out while analyzing the question paper. Please try again.",
        )

    except CohereAPIError as e:
        logger.error("Cohere API error for import %s: %s", import_id, e)
        await crud.update_question_import_failure(
            import_id,
            error_category="PROVIDER_ERROR",
            error_message="AI service encountered an issue processing the paper. Please try again.",
        )

    except Exception as e:
        logger.exception("Unexpected error processing import %s: %s", import_id, e)
        await crud.update_question_import_failure(
            import_id,
            error_category="INTERNAL_ERROR",
            error_message="An unexpected error occurred while processing the question paper.",
        )


async def confirm_question_import(
    import_id: str,
    current_user: UserResponse,
) -> QuestionImportConfirmResponse:
    """Transactionally creates ExamArena Question and Option rows from approved draft."""
    record = await crud.get_question_import_by_id(import_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question import not found",
        )

    # Idempotency check: if already completed, return existing success state without duplicating
    if record.status == QuestionImportStatus.COMPLETED:
        logger.info("QuestionImport %s is already COMPLETED. Returning idempotent confirmation.", import_id)
        # Count existing questions or return 0
        return QuestionImportConfirmResponse(
            id=record.id,
            examId=record.examId,
            status=QuestionImportStatus.COMPLETED,
            createdQuestionsCount=0,
            confirmedAt=record.confirmedAt or utc_now(),
        )

    if record.status != QuestionImportStatus.NEEDS_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot confirm import in '{record.status}' state. Only imports in 'NEEDS_REVIEW' can be confirmed.",
        )

    if not record.validatedExtraction or not isinstance(record.validatedExtraction, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid question draft found for confirmation",
        )

    try:
        paper = ExtractedQuestionPaper.model_validate(record.validatedExtraction)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Corrupt or invalid question draft schema: {str(e)}",
        )

    if not paper.questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question draft contains 0 questions. Cannot import an empty question paper.",
        )

    # Strict question validation before confirmation
    for idx, q in enumerate(paper.questions, start=1):
        q_label = f"Question {q.question_number or idx}"

        # 1. Reject UNKNOWN question types
        if q.question_type == ExtractedQuestionType.UNKNOWN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{q_label} has an UNKNOWN question type. Please select a valid question type before confirming.",
            )

        # 2. Validate marks
        if q.marks is None or q.marks <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{q_label} is missing positive marks. Please assign marks before confirming.",
            )

        # 3. Validate options for objective types
        if q.question_type in (
            ExtractedQuestionType.MULTIPLE_CHOICE,
            ExtractedQuestionType.MULTIPLE_SELECT,
            ExtractedQuestionType.TRUE_FALSE,
        ):
            if len(q.options) < 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{q_label} must have at least 2 options.",
                )
            if q.question_type == ExtractedQuestionType.TRUE_FALSE and len(q.options) != 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{q_label} is True/False and must have exactly 2 options.",
                )
            for opt_idx, opt in enumerate(q.options, start=1):
                if not opt.text.strip():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"{q_label}, Option {opt_idx} cannot be empty.",
                    )

    # Transactional DB creation
    created_count = 0
    now = utc_now()

    async with db.get_session() as session:
        async with session.begin():
            # Check exam exists
            exam_stmt = select(Exam).where(Exam.id == record.examId)
            exam = (await session.execute(exam_stmt)).scalar_one_or_none()
            if not exam:
                raise HTTPException(status_code=404, detail="Associated exam not found")

            # Calculate current highest question number
            max_q_stmt = select(func.max(Question.questionNumber)).where(
                Question.examId == record.examId
            )
            curr_max_q = (await session.execute(max_q_stmt)).scalar() or 0

            # Existing sections for this exam
            sec_stmt = select(ExamSection).where(ExamSection.examId == record.examId)
            existing_sections = {
                sec.name: sec for sec in (await session.execute(sec_stmt)).scalars().all()
            }

            max_sec_order_stmt = select(func.max(ExamSection.sortOrder)).where(
                ExamSection.examId == record.examId
            )
            curr_max_sec_order = (await session.execute(max_sec_order_stmt)).scalar() or 0

            # Insert questions
            for idx, q in enumerate(paper.questions, start=1):
                curr_max_q += 1
                sec_name = (q.section or "Section A").strip()
                db_q_type = map_extracted_type_to_model(q.question_type)
                q_marks = int(round(q.marks or 1))

                # Find or create section
                section_record = existing_sections.get(sec_name)
                if not section_record:
                    curr_max_sec_order += 1
                    section_record = ExamSection(
                        name=sec_name,
                        examId=record.examId,
                        questionType=db_q_type,
                        marksPerQuestion=q_marks,
                        sortOrder=curr_max_sec_order,
                    )
                    session.add(section_record)
                    await session.flush()  # populate section_record.id
                    existing_sections[sec_name] = section_record

                question_entity = Question(
                    examId=record.examId,
                    questionNumber=curr_max_q,
                    text=q.text.strip(),
                    marks=q_marks,
                    section=sec_name,
                    sectionId=section_record.id,
                    questionType=db_q_type,
                    explanation=q.instructions,
                )
                session.add(question_entity)
                await session.flush()  # populate question_entity.id

                # Add options if objective
                if db_q_type in (
                    QuestionType.MULTIPLE_CHOICE,
                    QuestionType.MULTIPLE_SELECT,
                    QuestionType.TRUE_FALSE,
                ):
                    for opt_idx, opt in enumerate(q.options, start=1):
                        # Phase 1: isCorrect defaults to False unless explicitly set during teacher review
                        is_correct = bool(opt.is_correct) if opt.is_correct is not None else False
                        opt_entity = QuestionOption(
                            questionId=question_entity.id,
                            optionNumber=opt_idx,
                            text=opt.text.strip(),
                            isCorrect=is_correct,
                        )
                        session.add(opt_entity)

                created_count += 1

            # Update import record status
            record_stmt = select(QuestionImport).where(QuestionImport.id == import_id)
            import_to_update = (await session.execute(record_stmt)).scalar_one()
            import_to_update.status = QuestionImportStatus.COMPLETED
            import_to_update.confirmedAt = now
            import_to_update.updatedAt = now

    # Record audit event
    await record_audit_event(
        action=AuditAction.QUESTION_CREATED,
        resource_type=AuditResourceType.EXAM,
        resource_id=record.examId,
        metadata={
            "importId": import_id,
            "createdQuestionsCount": created_count,
            "originalFileName": record.originalFileName,
        },
    )

    return QuestionImportConfirmResponse(
        id=record.id,
        examId=record.examId,
        status=QuestionImportStatus.COMPLETED,
        createdQuestionsCount=created_count,
        confirmedAt=now,
    )
