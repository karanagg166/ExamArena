"""FastAPI router for Course Materials management and semantic search."""

from __future__ import annotations

import logging
from typing import Annotated, Any
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.models import (
    CourseMaterialDocumentType,
    CourseMaterialStatus,
    Subject,
)
from app.course_materials import crud
from app.course_materials.permissions import (
    resolve_teacher_school_affiliation,
    resolve_user_search_school_id,
)
from app.course_materials.schemas import (
    CourseMaterialAnswerRequest,
    CourseMaterialAnswerResponse,
    CourseMaterialListResponse,
    CourseMaterialResponse,
    CourseMaterialSearchRequest,
    CourseMaterialSearchResponse,
    CourseMaterialStatusRefreshResponse,
)
from app.course_materials.service import CourseMaterialService
from app.users.schemas import UserResponse

logger = logging.getLogger("exam_arena.course_materials.router")

router = APIRouter(prefix="/api/v1/course-materials", tags=["course-materials"])


def get_course_material_service() -> CourseMaterialService:
    return CourseMaterialService()


@router.post(
    "/upload",
    response_model=CourseMaterialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest course material document",
)
async def upload_course_material(
    title: Annotated[str, Form(...)],
    subject: Annotated[Subject, Form(...)],
    file: UploadFile = File(...),
    document_type: Annotated[CourseMaterialDocumentType, Form()] = CourseMaterialDocumentType.OTHER,
    class_id: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
    db: AsyncSession = Depends(get_db),
    service: CourseMaterialService = Depends(get_course_material_service),
) -> CourseMaterialResponse:
    """
    Teacher or Admin uploads a syllabus/textbook/notes document.
    File is ingested into Search-Sphere within the authenticated school tenant.
    """
    school_id, _ = await resolve_teacher_school_affiliation(current_user, session=db)
    return await service.upload_course_material(
        session=db,
        school_id=school_id,
        uploaded_by_user_id=current_user.id,
        subject=subject,
        title=title,
        file=file,
        document_type=document_type,
        class_id=class_id,
        description=description,
    )


@router.get(
    "",
    response_model=CourseMaterialListResponse,
    status_code=status.HTTP_200_OK,
    summary="List course materials within authenticated school",
)
async def list_course_materials(
    subject: Subject | None = Query(None, description="Filter by subject"),
    class_id: str | None = Query(None, description="Filter by class"),
    status_filter: CourseMaterialStatus | None = Query(None, alias="status", description="Filter by status"),
    document_type: CourseMaterialDocumentType | None = Query(None, description="Filter by document type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
    db: AsyncSession = Depends(get_db),
) -> CourseMaterialListResponse:
    """List materials scoped strictly to authenticated school tenant."""
    school_id = await resolve_user_search_school_id(current_user, requested_class_id=class_id, session=db)
    items, total = await crud.list_course_materials(
        session=db,
        school_id=school_id,
        subject=subject,
        class_id=class_id,
        status=status_filter,
        document_type=document_type,
        limit=limit,
        offset=offset,
    )
    return CourseMaterialListResponse(
        total=total,
        items=[CourseMaterialResponse.model_validate(item) for item in items],
    )


@router.get(
    "/{material_id}",
    response_model=CourseMaterialResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single course material metadata",
)
async def get_course_material(
    material_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
    db: AsyncSession = Depends(get_db),
) -> CourseMaterialResponse:
    school_id = await resolve_user_search_school_id(current_user, requested_class_id=None, session=db)
    material = await crud.get_course_material_by_id(db, material_id)
    if not material or material.schoolId != school_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course material '{material_id}' not found.",
        )
    return CourseMaterialResponse.model_validate(material)


@router.post(
    "/{material_id}/refresh-status",
    response_model=CourseMaterialStatusRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh Search-Sphere document indexing status",
)
async def refresh_course_material_status(
    material_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
    db: AsyncSession = Depends(get_db),
    service: CourseMaterialService = Depends(get_course_material_service),
) -> CourseMaterialStatusRefreshResponse:
    school_id, _ = await resolve_teacher_school_affiliation(current_user, session=db)
    return await service.refresh_status(
        session=db,
        material_id=material_id,
        school_id=school_id,
    )


@router.delete(
    "/{material_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete course material from Search-Sphere and ExamArena",
)
async def delete_course_material(
    material_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
    db: AsyncSession = Depends(get_db),
    service: CourseMaterialService = Depends(get_course_material_service),
) -> dict[str, Any]:
    school_id, _ = await resolve_teacher_school_affiliation(current_user, session=db)
    success = await service.delete_course_material(
        session=db,
        material_id=material_id,
        school_id=school_id,
    )
    return {
        "success": success,
        "message": f"Course material '{material_id}' deleted successfully.",
    }


@router.post(
    "/search",
    response_model=CourseMaterialSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic search across course materials",
)
async def search_course_materials(
    body: CourseMaterialSearchRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
    db: AsyncSession = Depends(get_db),
    service: CourseMaterialService = Depends(get_course_material_service),
) -> CourseMaterialSearchResponse:
    """
    Search course materials using Search-Sphere hybrid semantic retrieval.
    Enforces school tenant isolation for teacher and student callers.
    """
    school_id = await resolve_user_search_school_id(
        current_user, requested_class_id=body.class_id, session=db
    )
    return await service.search_materials(
        school_id=school_id,
        query=body.query,
        subject=body.subject,
        class_id=body.class_id,
        document_type=body.document_type,
        limit=body.limit,
    )


@router.post(
    "/answer",
    response_model=CourseMaterialAnswerResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate grounded question answer from course materials",
)
async def answer_course_materials(
    body: CourseMaterialAnswerRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
    db: AsyncSession = Depends(get_db),
    service: CourseMaterialService = Depends(get_course_material_service),
) -> CourseMaterialAnswerResponse:
    """
    Generate grounded answer for a question over uploaded course materials using Search-Sphere.
    Enforces tenant isolation for teachers, principals, and students.
    """
    school_id = await resolve_user_search_school_id(
        current_user, requested_class_id=body.class_id, session=db
    )
    return await service.answer_question(
        session=db,
        school_id=school_id,
        query=body.query,
        subject=body.subject,
        class_id=body.class_id,
        document_type=body.document_type,
        limit=body.limit,
    )

