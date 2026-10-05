"""FastAPI router for Answer Key Imports."""

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
from app.ai.schemas.answer_key import MatchedAnswerKey, MatchStatus
from app.answer_keys import crud
from app.answer_keys.permissions import require_exam_answer_key_access
from app.answer_keys.schemas import (
    AnswerKeyImportConfirmRequest,
    AnswerKeyImportConfirmResponse,
    AnswerKeyImportListItem,
    AnswerKeyImportResponse,
    AnswerKeyImportUpdateRequest,
)
from app.answer_keys.service import (
    confirm_answer_key_import,
    format_answer_key_response,
    process_answer_key_import,
)
from app.api.deps import get_current_user
from app.audit.actions import AuditAction, AuditResourceType
from app.audit.service import record_audit_event
from app.core.config import settings
from app.core.models import (
    AnswerKeyImportSourceType,
    AnswerKeyImportStatus,
)
from app.storage.service import get_storage_provider
from app.users.schemas import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["answer-key-imports"])


@router.post(
    "/api/v1/exams/{exam_id}/answer-key-imports",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AnswerKeyImportResponse,
)
async def upload_answer_key(
    exam_id: str,
    file: UploadFile = File(...),
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """Upload an answer key (PDF, PNG, JPG, JPEG) to extract answers and rubrics asynchronously."""
    teacher, exam = await require_exam_answer_key_access(current_user, exam_id)
    teacher_id = teacher.id if teacher else exam.teacherId

    content = await file.read()

    try:
        clean_ext, verified_mime = validate_uploaded_file(
            filename=file.filename or "answer_key",
            declared_content_type=file.content_type or "application/octet-stream",
            file_bytes=content,
            max_mb=settings.QUESTION_IMPORT_MAX_FILE_MB,
        )
    except DocumentValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

    storage = get_storage_provider()
    storage_res = await storage.save_file(
        content=content,
        extension=clean_ext,
        directory=f"answer_keys/exam_{exam_id}",
    )

    initial_source_type = (
        AnswerKeyImportSourceType.PDF_TEXT
        if "pdf" in verified_mime
        else AnswerKeyImportSourceType.IMAGE
    )

    import_record = await crud.create_answer_key_import(
        exam_id=exam_id,
        teacher_id=teacher_id,
        original_file_name=file.filename or f"answer_key{clean_ext}",
        file_type=verified_mime,
        file_size=len(content),
        file_path=storage_res.key,
        source_type=initial_source_type,
        storage_provider=storage_res.provider,
        storage_key=storage_res.key,
        storage_url=storage_res.url,
        storage_resource_type=storage_res.resource_type,
    )

    await record_audit_event(
        action=AuditAction.QUESTION_UPDATED,
        resource_type=AuditResourceType.EXAM,
        resource_id=exam_id,
        metadata={
            "importId": import_record.id,
            "type": "answer_key_upload",
            "filename": import_record.originalFileName,
            "fileSize": import_record.fileSize,
        },
    )

    background_tasks.add_task(process_answer_key_import, import_record.id)

    return format_answer_key_response(import_record)


@router.get(
    "/api/v1/answer-key-imports/{import_id}",
    response_model=AnswerKeyImportResponse,
)
async def get_answer_key_import(
    import_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
):
    """Retrieve details and extraction status of an answer key import."""
    record = await crud.get_answer_key_import_by_id(import_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer key import job not found",
        )

    await require_exam_answer_key_access(current_user, record.examId)
    return format_answer_key_response(record)


@router.get(
    "/api/v1/exams/{exam_id}/answer-key-imports",
    response_model=list[AnswerKeyImportListItem],
)
async def list_exam_answer_key_imports(
    exam_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
):
    """List all answer key import attempts for a specific exam."""
    await require_exam_answer_key_access(current_user, exam_id)
    records = await crud.list_answer_key_imports_by_exam_id(exam_id)

    items: list[AnswerKeyImportListItem] = []
    for r in records:
        matched_cnt = 0
        total_cnt = 0
        if r.validatedExtraction and isinstance(r.validatedExtraction, dict):
            matched_cnt = r.validatedExtraction.get("matched_count", 0)
            total_cnt = r.validatedExtraction.get("total_answers", 0)

        items.append(
            AnswerKeyImportListItem(
                id=r.id,
                examId=r.examId,
                teacherId=r.teacherId,
                originalFileName=r.originalFileName,
                fileType=r.fileType,
                fileSize=r.fileSize,
                status=r.status,
                sourceType=r.sourceType,
                matchedCount=matched_cnt,
                totalAnswers=total_cnt,
                createdAt=r.createdAt,
                updatedAt=r.updatedAt,
                completedAt=r.completedAt,
                confirmedAt=r.confirmedAt,
            )
        )
    return items


@router.patch(
    "/api/v1/answer-key-imports/{import_id}",
    response_model=AnswerKeyImportResponse,
)
async def update_answer_key_import_draft(
    import_id: str,
    payload: AnswerKeyImportUpdateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
):
    """Update draft matched answers (e.g. resolve ambiguities or assign question IDs) prior to confirmation."""
    record = await crud.get_answer_key_import_by_id(import_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer key import job not found",
        )

    await require_exam_answer_key_access(current_user, record.examId)

    if record.status != AnswerKeyImportStatus.NEEDS_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot edit answer key import in '{record.status}' status. Only drafts in NEEDS_REVIEW can be modified.",
        )

    current_val = record.validatedExtraction or {}
    updated_answers = payload.answers if payload.answers is not None else [
        a for a in current_val.get("answers", [])
    ]

    matched_cnt = sum(
        1 for a in updated_answers
        if (a.status == MatchStatus.MATCHED or getattr(a, "status", None) == MatchStatus.MATCHED)
    )
    ambiguous_cnt = sum(
        1 for a in updated_answers
        if (a.status == MatchStatus.AMBIGUOUS or getattr(a, "status", None) == MatchStatus.AMBIGUOUS)
    )
    unmatched_cnt = sum(
        1 for a in updated_answers
        if (a.status == MatchStatus.UNMATCHED or getattr(a, "status", None) == MatchStatus.UNMATCHED)
    )

    answers_dump = [
        (a.model_dump() if hasattr(a, "model_dump") else a)
        for a in updated_answers
    ]

    new_extraction = dict(current_val)
    new_extraction["answers"] = answers_dump
    new_extraction["matched_count"] = matched_cnt
    new_extraction["ambiguous_count"] = ambiguous_cnt
    new_extraction["unmatched_count"] = unmatched_cnt
    new_extraction["total_answers"] = len(updated_answers)
    if payload.title is not None:
        new_extraction["title"] = payload.title

    updated_record = await crud.update_answer_key_import_draft(
        import_id=import_id,
        validated_extraction=new_extraction,
    )
    return format_answer_key_response(updated_record or record)


@router.post(
    "/api/v1/answer-key-imports/{import_id}/confirm",
    response_model=AnswerKeyImportConfirmResponse,
)
async def confirm_answer_key_import_endpoint(
    import_id: str,
    payload: AnswerKeyImportConfirmRequest = AnswerKeyImportConfirmRequest(),
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
):
    """Confirm and transactionally apply matched answers to the exam questions."""
    record = await crud.get_answer_key_import_by_id(import_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer key import job not found",
        )

    await require_exam_answer_key_access(current_user, record.examId)

    return await confirm_answer_key_import(
        import_id=import_id,
        user_id=current_user.id,
        overwrite_existing=payload.overwriteExistingAnswers,
        edited_answers=payload.answers,
    )
