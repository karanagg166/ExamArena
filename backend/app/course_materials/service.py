"""Course Materials business logic and Search-Sphere synchronization."""

from __future__ import annotations

import logging
from typing import Any
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    CourseMaterial,
    CourseMaterialDocumentType,
    CourseMaterialStatus,
    Subject,
)
from app.course_materials import crud
from app.course_materials.schemas import (
    CourseMaterialResponse,
    CourseMaterialSearchResponse,
    CourseMaterialSearchResultItem,
    CourseMaterialStatusRefreshResponse,
)
from app.integrations.search_sphere.client import (
    SearchSphereClient,
    get_search_sphere_client,
)
from app.integrations.search_sphere.exceptions import (
    SearchSphereError,
    SearchSphereNotFoundError,
)
from app.integrations.search_sphere.identifiers import (
    build_collection_id,
    build_external_document_id,
    build_owner_subject_id,
    build_tenant_id,
)

logger = logging.getLogger("exam_arena.course_materials.service")

MAX_COURSE_MATERIAL_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_MIME_TYPES = {"application/pdf"}


def validate_material_file(file_bytes: bytes, filename: str, content_type: str | None) -> str:
    """Validate that uploaded file is a valid, non-empty PDF within bounds."""
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content cannot be empty.",
        )
    if len(file_bytes) > MAX_COURSE_MATERIAL_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_COURSE_MATERIAL_SIZE_BYTES // (1024 * 1024)} MB.",
        )

    # Validate PDF magic bytes
    if not file_bytes.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF documents are currently supported for course materials.",
        )

    return "application/pdf"


class CourseMaterialService:
    def __init__(self, search_sphere_client: SearchSphereClient | None = None):
        self._ss_client = search_sphere_client or get_search_sphere_client()

    async def upload_course_material(
        self,
        session: AsyncSession,
        school_id: str,
        uploaded_by_user_id: str,
        subject: Subject,
        title: str,
        file: UploadFile,
        document_type: CourseMaterialDocumentType = CourseMaterialDocumentType.OTHER,
        class_id: str | None = None,
        description: str | None = None,
    ) -> CourseMaterialResponse:
        """
        Upload course material file, ensure Search-Sphere collection,
        upload file bytes to Search-Sphere, register document, and save local metadata.
        """
        file_bytes = await file.read()
        filename = file.filename or "course_material.pdf"
        mime_type = validate_material_file(file_bytes, filename, file.content_type)
        file_size = len(file_bytes)

        # 1. Derive Search-Sphere deterministic identifiers
        tenant_id = build_tenant_id(school_id)
        collection_id = build_collection_id(subject=subject, class_id=class_id)
        owner_subject_id = build_owner_subject_id(uploaded_by_user_id)

        # 2. Idempotently ensure Search-Sphere collection exists
        collection_name = (
            f"Class {class_id} - {subject.value}"
            if class_id
            else f"{subject.value} Materials"
        )
        try:
            await self._ss_client.ensure_collection(
                collection_id=collection_id,
                name=collection_name,
                description=f"Course materials for {subject.value} in school {school_id}",
                tenant_id=tenant_id,
            )
        except SearchSphereError as exc:
            logger.error("Failed ensuring collection in Search-Sphere: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Unable to provision collection in Search-Sphere: {exc.message}",
            ) from exc

        # 3. Create local record in UPLOADED state
        material = await crud.create_course_material(
            session=session,
            school_id=school_id,
            subject=subject,
            uploaded_by=uploaded_by_user_id,
            title=title,
            original_file_name=filename,
            file_size=file_size,
            mime_type=mime_type,
            document_type=document_type,
            search_sphere_collection_id=collection_id,
            class_id=class_id,
            description=description,
            status=CourseMaterialStatus.UPLOADED,
        )

        external_doc_id = build_external_document_id(material.id)

        # 4. Upload file bytes to Search-Sphere storage & register document
        try:
            upload_res = await self._ss_client.upload_file(
                file_bytes=file_bytes,
                filename=filename,
                content_type=mime_type,
                document_id=external_doc_id,
                collection_id=collection_id,
                tenant_id=tenant_id,
            )
            storage_key = upload_res["storage_key"]

            doc_res = await self._ss_client.register_document(
                external_document_id=external_doc_id,
                storage_key=storage_key,
                file_name=filename,
                mime_type=mime_type,
                file_size=file_size,
                collection_id=collection_id,
                owner_subject_id=owner_subject_id,
                document_type=document_type.value,
                metadata={
                    "exam_arena_material_id": material.id,
                    "school_id": school_id,
                    "subject": subject.value,
                    "class_id": class_id,
                    "uploaded_by": uploaded_by_user_id,
                },
                tenant_id=tenant_id,
            )

            ss_doc_id = doc_res.get("id")
            ss_status = doc_res.get("status", "QUEUED")
            mapped_status = (
                CourseMaterialStatus.READY
                if ss_status == "READY"
                else CourseMaterialStatus.PROCESSING
            )

            updated = await crud.update_course_material_status(
                session=session,
                material_id=material.id,
                status=mapped_status,
                search_sphere_document_id=ss_doc_id,
            )
            return CourseMaterialResponse.model_validate(updated)

        except Exception as exc:
            err_msg = str(getattr(exc, "message", str(exc)))
            logger.error("Failed indexing material %s in Search-Sphere: %s", material.id, err_msg)
            # Safe failure compensation: update local row to FAILED
            await crud.update_course_material_status(
                session=session,
                material_id=material.id,
                status=CourseMaterialStatus.FAILED,
                processing_error=f"Search-Sphere ingestion failure: {err_msg}",
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Course material ingestion failed: {err_msg}",
            ) from exc

    async def refresh_status(
        self,
        session: AsyncSession,
        material_id: str,
        school_id: str,
    ) -> CourseMaterialStatusRefreshResponse:
        """Query Search-Sphere document status and synchronize local record."""
        material = await crud.get_course_material_by_id(session, material_id)
        if not material or material.schoolId != school_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course material '{material_id}' not found.",
            )

        if not material.searchSphereDocumentId:
            return CourseMaterialStatusRefreshResponse(
                material_id=material.id,
                status=material.status,
                search_sphere_document_id=None,
                processing_error=material.processingError,
            )

        tenant_id = build_tenant_id(school_id)
        try:
            doc_info = await self._ss_client.get_document(
                document_id=material.searchSphereDocumentId,
                tenant_id=tenant_id,
            )
            raw_status = doc_info.get("status", "PROCESSING")
            raw_error = doc_info.get("processing_error")

            mapped_status = CourseMaterialStatus.PROCESSING
            if raw_status == "READY":
                mapped_status = CourseMaterialStatus.READY
            elif raw_status == "FAILED":
                mapped_status = CourseMaterialStatus.FAILED

            updated = await crud.update_course_material_status(
                session=session,
                material_id=material.id,
                status=mapped_status,
                processing_error=raw_error,
            )
            return CourseMaterialStatusRefreshResponse(
                material_id=material.id,
                status=updated.status if updated else mapped_status,
                search_sphere_document_id=material.searchSphereDocumentId,
                processing_error=raw_error,
            )
        except SearchSphereNotFoundError:
            updated = await crud.update_course_material_status(
                session=session,
                material_id=material.id,
                status=CourseMaterialStatus.FAILED,
                processing_error="Document record missing in Search-Sphere.",
            )
            return CourseMaterialStatusRefreshResponse(
                material_id=material.id,
                status=CourseMaterialStatus.FAILED,
                search_sphere_document_id=material.searchSphereDocumentId,
                processing_error="Document record missing in Search-Sphere.",
            )
        except SearchSphereError as exc:
            logger.warning("Could not refresh Search-Sphere status: %s", exc)
            return CourseMaterialStatusRefreshResponse(
                material_id=material.id,
                status=material.status,
                search_sphere_document_id=material.searchSphereDocumentId,
                processing_error=material.processingError,
            )

    async def delete_course_material(
        self,
        session: AsyncSession,
        material_id: str,
        school_id: str,
    ) -> bool:
        """Delete document from Search-Sphere and remove local ExamArena metadata."""
        material = await crud.get_course_material_by_id(session, material_id)
        if not material or material.schoolId != school_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course material '{material_id}' not found.",
            )

        tenant_id = build_tenant_id(school_id)

        # 1. Delete upstream in Search-Sphere
        if material.searchSphereDocumentId:
            try:
                await self._ss_client.delete_document(
                    document_id=material.searchSphereDocumentId,
                    tenant_id=tenant_id,
                )
            except SearchSphereNotFoundError:
                logger.info(
                    "Document %s was already deleted in Search-Sphere",
                    material.searchSphereDocumentId,
                )
            except SearchSphereError as exc:
                logger.warning(
                    "Failed upstream Search-Sphere document deletion for %s: %s",
                    material.id,
                    exc,
                )

        # 2. Delete local metadata
        return await crud.delete_course_material(session, material.id)

    async def search_materials(
        self,
        school_id: str,
        query: str,
        subject: Subject,
        class_id: str | None = None,
        document_type: CourseMaterialDocumentType | None = None,
        limit: int = 10,
    ) -> CourseMaterialSearchResponse:
        """
        Execute semantic search against Search-Sphere within authenticated school tenant.
        """
        tenant_id = build_tenant_id(school_id)
        collection_id = build_collection_id(subject=subject, class_id=class_id)

        try:
            raw_res = await self._ss_client.search(
                query=query,
                collection_id=collection_id,
                limit=limit,
                document_type=document_type.value if document_type else None,
                tenant_id=tenant_id,
            )

            results: list[CourseMaterialSearchResultItem] = []
            for item in raw_res.get("results", []):
                results.append(
                    CourseMaterialSearchResultItem(
                        chunk_id=item.get("chunk_id", ""),
                        search_sphere_document_id=item.get("document_id", ""),
                        material_id=item.get("metadata", {}).get("exam_arena_material_id")
                        if isinstance(item.get("metadata"), dict)
                        else None,
                        file_name=item.get("file_name"),
                        document_type=item.get("document_type"),
                        text=item.get("text", ""),
                        score=float(item.get("score", 0.0)),
                        rank=int(item.get("rank", 0)),
                        start_page=item.get("start_page"),
                        end_page=item.get("end_page"),
                    )
                )

            return CourseMaterialSearchResponse(
                query=raw_res.get("query", query),
                total=raw_res.get("total", len(results)),
                results=results,
                duration_ms=float(raw_res.get("duration_ms", 0.0)),
            )
        except SearchSphereError as exc:
            logger.error("Search-Sphere search query failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Semantic search service error: {exc.message}",
            ) from exc
