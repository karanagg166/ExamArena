"""Pydantic schemas for Course Materials domain."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.models import CourseMaterialDocumentType, CourseMaterialStatus, Subject


class CourseMaterialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str = Field(..., alias="schoolId")
    subject: Subject
    class_id: str | None = Field(None, alias="classId")
    uploaded_by: str = Field(..., alias="uploadedBy")
    title: str
    description: str | None = None
    original_file_name: str = Field(..., alias="originalFileName")
    file_size: int = Field(..., alias="fileSize")
    mime_type: str = Field(..., alias="mimeType")
    document_type: CourseMaterialDocumentType = Field(..., alias="documentType")
    search_sphere_document_id: str | None = Field(None, alias="searchSphereDocumentId")
    search_sphere_collection_id: str = Field(..., alias="searchSphereCollectionId")
    status: CourseMaterialStatus
    processing_error: str | None = Field(None, alias="processingError")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class CourseMaterialListResponse(BaseModel):
    total: int
    items: list[CourseMaterialResponse]


class CourseMaterialStatusRefreshResponse(BaseModel):
    material_id: str
    status: CourseMaterialStatus
    search_sphere_document_id: str | None = None
    processing_error: str | None = None


class CourseMaterialSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="Natural language search query")
    subject: Subject = Field(..., description="Target academic subject")
    class_id: str | None = Field(None, description="Optional specific class scope")
    document_type: CourseMaterialDocumentType | None = Field(
        None, description="Optional document type filter"
    )
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of search chunks")


class CourseMaterialSearchResultItem(BaseModel):
    chunk_id: str
    search_sphere_document_id: str
    material_id: str | None = None
    file_name: str | None = None
    document_type: str | None = None
    text: str
    score: float
    rank: int
    start_page: int | None = None
    end_page: int | None = None


class CourseMaterialSearchResponse(BaseModel):
    query: str
    total: int
    results: list[CourseMaterialSearchResultItem]
    duration_ms: float


class CourseMaterialAnswerRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    query: str = Field(..., min_length=1, max_length=2000, description="Question about course materials")
    subject: Subject = Field(..., description="Target academic subject")
    class_id: str | None = Field(None, alias="classId", description="Optional specific class scope")
    document_type: CourseMaterialDocumentType | None = Field(
        None, alias="documentType", description="Optional document type filter"
    )
    limit: int = Field(default=5, ge=1, le=20, description="Number of context chunks to retrieve")


class CourseMaterialAnswerCitation(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    citation_number: int = Field(..., alias="citationNumber")
    file_name: str | None = Field(None, alias="fileName")
    title: str | None = None
    page_number: int | None = Field(None, alias="pageNumber")
    text_snippet: str = Field(..., alias="textSnippet")
    material_id: str | None = Field(None, alias="materialId")
    document_type: str | None = Field(None, alias="documentType")


class CourseMaterialAnswerResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    answer: str
    citations: list[CourseMaterialAnswerCitation] = Field(default_factory=list)
    retrieved_chunk_count: int = Field(default=0, alias="retrievedChunkCount")
    warnings: list[str] = Field(default_factory=list)
    duration_ms: float = Field(default=0.0, alias="durationMs")

