"""FastAPI router for Question Paper Imports."""

import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from app.ai.extraction.document import (
    DocumentValidationError,
    validate_uploaded_file,
)
from app.ai.schemas.question_paper import (
    ExtractedQuestionPaper,
)
from app.api.deps import get_current_user
from app.audit.actions import AuditAction, AuditResourceType
from app.audit.service import record_audit_event
from app.core.config import settings
from app.core.models import (
    QuestionImportSourceType,
    QuestionImportStatus,
    utc_now,
)
from app.imports import crud
from app.imports.permissions import require_exam_import_access
from app.imports.schemas import (
    QuestionImportConfirmResponse,
    QuestionImportListItem,
    QuestionImportResponse,
    QuestionImportUpdateRequest,
)
from app.imports.service import (
    confirm_question_import,
    format_import_response,
    process_question_import,
)
from app.imports.worker import (
    WORKER_HEARTBEAT_KEY,
    check_worker_availability,
    get_redis_settings,
)
from app.storage.service import get_storage_provider
from app.users.schemas import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["question-imports"])


async def dispatch_import_job(
    import_id: str, background_tasks: BackgroundTasks
) -> str:
    """Dispatches question paper import job to ARQ queue when an active worker is present,

    otherwise falls back to in-process background tasks with explicit operational logging.
    Returns the dispatch mode: 'arq_worker' or 'in_process_background_task'.
    """
    if settings.REDIS_URL:
        try:
            from arq import create_pool

            pool = await create_pool(get_redis_settings())
            try:
                health = await pool.get("arq:queue:health-check")
                heartbeat = await pool.get(WORKER_HEARTBEAT_KEY)
                worker_active = bool(health or heartbeat)

                if worker_active:
                    job = await pool.enqueue_job("run_import_job", import_id)
                    logger.info(
                        "Enqueued QuestionImport %s to active ARQ worker (job_id: %s)",
                        import_id,
                        job.job_id if job else None,
                    )
                    return "arq_worker"
                else:
                    logger.warning(
                        "Redis reachable, but no active ARQ worker detected. "
                        "Falling back to ephemeral BackgroundTasks for import %s. "
                        "Note: In-process tasks will not survive container restarts.",
                        import_id,
                    )
            finally:
                await pool.aclose()
        except Exception as e:
            logger.warning(
                "Failed to enqueue to ARQ queue (%s). Falling back to background task.",
                e,
            )

    background_tasks.add_task(process_question_import, import_id)
    return "in_process_background_task"


@router.get("/api/v1/imports/worker-status")
async def get_worker_status(
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
):
    """Diagnostic endpoint to inspect background worker availability and queue health."""
    return await check_worker_availability()


@router.post(
    "/api/v1/exams/{exam_id}/question-imports",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=QuestionImportResponse,
)
async def upload_question_paper(
    exam_id: str,
    file: UploadFile = File(...),
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """Upload a question paper (PDF, PNG, JPG, JPEG) to extract questions asynchronously."""
    teacher, exam = await require_exam_import_access(current_user, exam_id)
    teacher_id = teacher.id if teacher else exam.teacherId

    # Read uploaded bytes
    content = await file.read()

    # Strict validation of magic bytes, extension, MIME type, and size
    try:
        clean_ext, verified_mime = validate_uploaded_file(
            filename=file.filename or "question_paper",
            declared_content_type=file.content_type or "application/octet-stream",
            file_bytes=content,
            max_mb=settings.QUESTION_IMPORT_MAX_FILE_MB,
        )
    except DocumentValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e)) from e

    # Save to storage provider
    storage = get_storage_provider()
    storage_res = await storage.save_file(
        content=content,
        extension=clean_ext,
        directory=f"exam_{exam_id}",
    )

    # Determine initial sourceType
    initial_source_type = (
        QuestionImportSourceType.PDF_TEXT
        if "pdf" in verified_mime
        else QuestionImportSourceType.IMAGE
    )

    # Create QuestionImport database record
    import_record = await crud.create_question_import(
        exam_id=exam_id,
        teacher_id=teacher_id,
        original_file_name=file.filename or f"paper{clean_ext}",
        file_type=verified_mime,
        file_size=len(content),
        file_path=storage_res.key,
        source_type=initial_source_type,
        storage_provider=storage_res.provider,
        storage_key=storage_res.key,
        storage_url=storage_res.url,
        storage_resource_type=storage_res.resource_type,
    )

    # Audit event
    await record_audit_event(
        action=AuditAction.QUESTION_CREATED,
        resource_type=AuditResourceType.EXAM,
        resource_id=exam_id,
        metadata={
            "importId": import_record.id,
            "filename": import_record.originalFileName,
            "fileSize": import_record.fileSize,
        },
    )

    # Dispatch asynchronous worker (durable ARQ if available, background task fallback)
    await dispatch_import_job(import_record.id, background_tasks)

    return format_import_response(import_record)


@router.get(
    "/api/v1/question-imports/{import_id}",
    response_model=QuestionImportResponse,
)
async def get_import_status(
    import_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
):
    """Retrieve import job status, progress, and extracted questions."""
    record = await crud.get_question_import_by_id(import_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question import not found",
        )

    # Ensure access to the associated exam
    await require_exam_import_access(current_user, record.examId)

    # Recover stuck PROCESSING jobs (> 300 seconds)
    if record.status == QuestionImportStatus.PROCESSING and record.updatedAt:
        now_ts = utc_now()
        updated_ts = record.updatedAt if record.updatedAt.tzinfo else record.updatedAt.replace(tzinfo=now_ts.tzinfo)
        elapsed = (now_ts - updated_ts).total_seconds()
        if elapsed > 300:
            logger.warning("Import %s stuck in PROCESSING for %.1fs. Transitioning to TIMEOUT failure.", import_id, elapsed)
            record = await crud.update_question_import_failure(
                import_id,
                error_category="TIMEOUT",
                error_message="Import processing timed out after 300 seconds. You may retry the import.",
            )

    return format_import_response(record)


@router.post(
    "/api/v1/question-imports/{import_id}/retry",
    response_model=QuestionImportResponse,
)
async def retry_question_import(
    import_id: str,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
):
    """Retry an import job that failed, timed out, or got stuck."""
    record = await crud.get_question_import_by_id(import_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question import not found",
        )

    await require_exam_import_access(current_user, record.examId)

    if record.status == QuestionImportStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot retry an already completed import.",
        )

    reset_record = await crud.reset_question_import_for_retry(import_id)
    await dispatch_import_job(import_id, background_tasks)
    return format_import_response(reset_record or record)


@router.get(
    "/api/v1/exams/{exam_id}/question-imports",
    response_model=list[QuestionImportListItem],
)
async def list_exam_imports(
    exam_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
):
    """List all previous question imports for an exam."""
    await require_exam_import_access(current_user, exam_id)
    records = await crud.list_question_imports_by_exam_id(exam_id)

    items: list[QuestionImportListItem] = []
    for r in records:
        q_count = 0
        if r.validatedExtraction and isinstance(r.validatedExtraction, dict):
            q_list = r.validatedExtraction.get("questions")
            if isinstance(q_list, list):
                q_count = len(q_list)

        items.append(
            QuestionImportListItem(
                id=r.id,
                examId=r.examId,
                teacherId=r.teacherId,
                originalFileName=r.originalFileName,
                fileType=r.fileType,
                fileSize=r.fileSize,
                status=r.status,
                sourceType=r.sourceType,
                questionCount=q_count,
                createdAt=r.createdAt,
                updatedAt=r.updatedAt,
                completedAt=r.completedAt,
                confirmedAt=r.confirmedAt,
            )
        )
    return items


@router.patch(
    "/api/v1/question-imports/{import_id}",
    response_model=QuestionImportResponse,
)
async def update_import_draft(
    import_id: str,
    payload: QuestionImportUpdateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
):
    """Update draft extracted questions during teacher review before confirmation."""
    record = await crud.get_question_import_by_id(import_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question import not found",
        )

    await require_exam_import_access(current_user, record.examId)

    if record.status != QuestionImportStatus.NEEDS_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot edit draft when import status is '{record.status}'.",
        )

    current_data = record.validatedExtraction or {}
    try:
        current_paper = ExtractedQuestionPaper.model_validate(current_data)
    except Exception:
        current_paper = ExtractedQuestionPaper()

    if payload.title is not None:
        current_paper.title = payload.title
    if payload.subject is not None:
        current_paper.subject = payload.subject
    if payload.questions is not None:
        current_paper.questions = payload.questions

    updated_dict = current_paper.model_dump()
    updated_record = await crud.update_question_import_draft(import_id, updated_dict)
    if not updated_record:
        raise HTTPException(status_code=404, detail="Failed to update import draft")

    return format_import_response(updated_record)


@router.post(
    "/api/v1/question-imports/{import_id}/confirm",
    response_model=QuestionImportConfirmResponse,
)
async def confirm_import(
    import_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
):
    """Confirm review and transactionally insert questions into ExamArena."""
    record = await crud.get_question_import_by_id(import_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question import not found",
        )

    await require_exam_import_access(current_user, record.examId)

    return await confirm_question_import(import_id, current_user)
