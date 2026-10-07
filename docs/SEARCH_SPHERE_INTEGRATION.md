# Search-Sphere Integration Guide

This document describes the architectural foundation, identity contracts, configuration, and security guarantees for ExamArena's integration with the Search-Sphere multi-tenant RAG microservice.

---

## 1. Purpose & Separation of Concerns

ExamArena acts purely as an authenticated client of Search-Sphere. 

- **Search-Sphere Owns**:
  - Document file storage in tenant-isolated object storage
  - Text extraction, cleaning, and chunking pipelines
  - Dense embeddings (FastEmbed) and sparse indices (BM25)
  - Vector storage and indexing in Qdrant
  - Reciprocal Rank Fusion (RRF) and Cross-Encoder reranking
  - Grounded LLM answer generation and citation synthesis
- **ExamArena Owns**:
  - User identity, roles (Teachers, Students, Principals, Admins), and course enrollment
  - Relational metadata for course materials (school affiliation, subject, class, uploader, status)
  - Server-side authorization and tenant boundary resolution
  - Triggering ingestion, polling status, and proxying semantic search queries

ExamArena does **not** install or execute vector database engines, embeddings, or retrieval algorithms locally.

---

## 2. Multi-Tenant Identity Model

All requests from ExamArena map to Search-Sphere's three-tier identity hierarchy:

| Tier | Mapping in ExamArena | Example |
| :--- | :--- | :--- |
| **Client Application** (`client_id`) | Constant: `exam_arena` | `exam_arena` |
| **Tenant** (`tenant_id`) | School ID: `school_<schoolId>` | `school_sch_12345` |
| **Collection** (`collection_id`) | Subject or Class + Subject: `subject_<subject>` or `class_<classId>_subject_<subject>` | `subject_science`, `class_cls_9_subject_maths` |
| **Subject / Owner** (`owner_subject_id`) | Uploader User ID: `user_<userId>` | `user_usr_9988` |
| **External Document** (`external_document_id`) | Local CourseMaterial ID: `<materialId>` | `cm_abc123` |

### Security Guarantees
- **Tenant Isolation**: School is the organizational isolation boundary. A teacher from School A can never read, ingest, or search materials belonging to School B.
- **Collection Isolation**: Materials for different subjects/classes map to distinct collections within each school tenant.
- **Tamper Protection**: Tenant IDs, client IDs, and collections are derived strictly on the ExamArena backend from authenticated session state; client headers or request body parameters cannot override them.

---

## 3. Server-Only Configuration

Search-Sphere credentials are strictly server-side and must never be exposed to the browser or client-side bundles.

Add the following to `.env`:

```env
# ─── Search-Sphere RAG Microservice ────────────────────────
SEARCH_SPHERE_URL="http://localhost:8000"
SEARCH_SPHERE_API_KEY="ss_live_YOUR_SEARCH_SPHERE_API_KEY"
SEARCH_SPHERE_CLIENT_ID="exam_arena"
SEARCH_SPHERE_TIMEOUT_SECONDS=30.0
```

> **Warning**: Never prefix these variables with `NEXT_PUBLIC_`. The frontend communicates exclusively with ExamArena API routes (`/api/v1/course-materials/...`), which proxy to Search-Sphere.

---

## 4. Endpoints & Integration Flows

All endpoints live under `/api/v1/course-materials`:

### 4.1 Ingestion Flow
1. Teacher submits `multipart/form-data` to `POST /api/v1/course-materials/upload`.
2. ExamArena verifies teacher role and resolves school affiliation.
3. ExamArena derives `tenant_id` (`school_<schoolId>`) and `collection_id` (`subject_<subject>`).
4. ExamArena calls `POST /api/v1/collections` in Search-Sphere to ensure the collection exists idempotently.
5. ExamArena persists a `CourseMaterial` row with status `UPLOADED`.
6. ExamArena uploads the file bytes to `POST /api/v1/documents/upload` in Search-Sphere, obtaining `storage_key`.
7. ExamArena calls `POST /api/v1/documents` in Search-Sphere to register document metadata and trigger async ingestion.
8. ExamArena updates the local row to `PROCESSING` (or `READY`) and stores `searchSphereDocumentId`.
9. If any upstream step fails, the local record is marked `FAILED` with `processingError` populated.

### 4.2 Status Refresh Flow
- `POST /api/v1/course-materials/{id}/refresh-status`
- Calls Search-Sphere `GET /api/v1/documents/{searchSphereDocumentId}`.
- Maps upstream status (`QUEUED` / `PROCESSING` / `READY` / `FAILED`) to local record.

### 4.3 Deletion Flow
- `DELETE /api/v1/course-materials/{id}`
- Calls Search-Sphere `DELETE /api/v1/documents/{searchSphereDocumentId}` with tenant scoping.
- Deletes local `CourseMaterial` database row.

### 4.4 Semantic Search Flow
- `POST /api/v1/course-materials/search`
- Accepts natural language query, subject, optional class scope, and limit.
- Validates user role and school boundary.
- Forwards to Search-Sphere `POST /api/v1/search` with authoritative `X-Tenant-ID` and collection scope.
- Returns relevance-ranked snippets with page numbers and document titles.

---

## 5. Running the Opt-in Integration Test

To verify end-to-end integration against a live running Search-Sphere microservice instance:

```bash
RUN_SEARCH_SPHERE_INTEGRATION=1 \
SEARCH_SPHERE_URL=http://localhost:8000 \
SEARCH_SPHERE_API_KEY=ss_live_... \
pytest backend/tests/integration/test_search_sphere_live.py -v
```

This synthetic test:
1. Provisions a test collection
2. Uploads and registers a synthetic PDF
3. Polls until indexing status is `READY`
4. Performs a semantic search for a known phrase
5. Deletes the test document and cleans up
