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
    Response,
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
    assert_material_response_access,
    resolve_cleanup_scope,
    resolve_teacher_school_affiliation,
    resolve_user_material_scope,
    resolve_user_search_school_id,
)
from app.course_materials.schemas import (
    CourseMaterialAnswerRequest,
    CourseMaterialAnswerResponse,
    CourseMaterialCleanupReceipt,
    CourseMaterialListResponse,
    CourseMaterialResponse,
    CourseMaterialSearchRequest,
    CourseMaterialSearchResponse,
    CourseMaterialStatusRefreshResponse,
)
from app.course_materials.service import CourseMaterialService
from app.integrations.search_sphere.client import (
    SearchSphereClient,
    get_search_sphere_client,
)
from app.integrations.search_sphere.exceptions import SearchSphereError
from app.integrations.search_sphere.identifiers import (
    build_external_document_id,
    build_tenant_id,
)
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
    document_type: Annotated[
        CourseMaterialDocumentType, Form()
    ] = CourseMaterialDocumentType.OTHER,
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
    await resolve_user_material_scope(current_user, class_id, db)
    result = await service.upload_course_material(
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

    await assert_material_response_access(current_user, school_id, class_id, db)
    return result


@router.get(
    "",
    response_model=CourseMaterialListResponse,
    status_code=status.HTTP_200_OK,
    summary="List course materials within authenticated school",
)
async def list_course_materials(
    subject: Subject | None = Query(None, description="Filter by subject"),
    class_id: str | None = Query(None, description="Filter by class"),
    status_filter: CourseMaterialStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
    document_type: CourseMaterialDocumentType | None = Query(
        None, description="Filter by document type"
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Annotated[UserResponse, Depends(get_current_user)] = None,
    db: AsyncSession = Depends(get_db),
) -> CourseMaterialListResponse:
    """List materials scoped strictly to authenticated school tenant."""
    school_id, visible_class_ids = await resolve_user_material_scope(
        current_user, requested_class_id=class_id, session=db
    )
    items, total = await crud.list_course_materials(
        session=db,
        school_id=school_id,
        subject=subject,
        class_id=class_id,
        status=status_filter,
        document_type=document_type,
        limit=limit,
        offset=offset,
        visible_class_ids=visible_class_ids,
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
    school_id, visible_class_ids = await resolve_user_material_scope(
        current_user, requested_class_id=None, session=db
    )
    material = await crud.get_course_material_by_id(
        db, material_id, school_id=school_id, visible_class_ids=visible_class_ids
    )
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
    _, visible_classes = await resolve_user_material_scope(current_user, None, db)
    material = await crud.get_course_material_by_id(
        db, material_id, school_id=school_id, visible_class_ids=visible_classes
    )
    if material is None:
        raise HTTPException(404, "Course material not found.")
    await resolve_user_material_scope(current_user, material.classId, db)
    result = await service.refresh_status(
        session=db,
        material_id=material_id,
        school_id=school_id,
    )

    await assert_material_response_access(current_user, school_id, material.classId, db)
    return result


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
    _, visible_classes = await resolve_user_material_scope(current_user, None, db)
    material = await crud.get_course_material_by_id(
        db, material_id, school_id=school_id, visible_class_ids=visible_classes
    )
    if material is None:
        raise HTTPException(404, "Course material not found.")
    await resolve_user_material_scope(current_user, material.classId, db)
    success = await service.delete_course_material(
        session=db,
        material_id=material_id,
        school_id=school_id,
    )
    await assert_material_response_access(current_user, school_id, material.classId, db)
    return {
        "success": success,
        "message": f"Course material '{material_id}' deleted successfully.",
    }


@router.get("/{material_id}/cleanup", response_model=CourseMaterialCleanupReceipt)
async def get_course_material_cleanup(
    material_id: str,
    response: Response,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    subject: Subject | None = Query(None),
    class_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    client: SearchSphereClient = Depends(get_search_sphere_client),
) -> CourseMaterialCleanupReceipt:
    """Staff can verify physical cleanup after local metadata was removed."""
    response.headers["Cache-Control"] = "private, no-store"
    school_id, _ = await resolve_teacher_school_affiliation(current_user, session=db)
    collection_id, class_id = await resolve_cleanup_scope(
        current_user, school_id, material_id, subject, class_id, db
    )
    try:
        document_id = build_external_document_id(material_id)
        value = await client.get_document_cleanup(
            document_id=document_id,
            tenant_id=build_tenant_id(school_id),
            collection_id=collection_id,
        )
        receipt = CourseMaterialCleanupReceipt.model_validate(value)
        if receipt.document_id != document_id:
            raise ValueError("Cleanup identity mismatch.")
        await assert_material_response_access(current_user, school_id, class_id, db)
        return receipt
    except SearchSphereError as exc:
        code = 404 if exc.status_code in {403, 404} else 503
        raise HTTPException(code, detail="Document cleanup is not verified.") from None
    except ValueError:
        raise HTTPException(
            503, detail="Document cleanup receipt is invalid."
        ) from None


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
    result = await service.search_materials(
        session=db,
        school_id=school_id,
        query=body.query,
        subject=body.subject,
        class_id=body.class_id,
        document_type=body.document_type,
        limit=body.limit,
    )
    await assert_material_response_access(current_user, school_id, body.class_id, db)
    return result


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
    result = await service.answer_question(
        session=db,
        school_id=school_id,
        query=body.query,
        subject=body.subject,
        class_id=body.class_id,
        document_type=body.document_type,
        limit=body.limit,
    )
    await assert_material_response_access(current_user, school_id, body.class_id, db)
    return result
