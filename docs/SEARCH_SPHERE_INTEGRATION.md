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

## Processing-state contract

Registration and refresh share one validated mapping: QUEUED/PENDING → UPLOADED,
PROCESSING → PROCESSING, READY → READY and FAILED → FAILED. Unknown/missing states
are upstream failures. Refresh returns HTTP 503 during an upstream outage and
preserves local metadata for retry; it does not report a successful stale refresh.
Successful processing clears a previous local processing error.


## Deployment contract gate

The post-deploy workflow runs only by trusted `main` dispatch after deployment, with
a required full `expected_sha`. The `search-sphere-release` environment permits only
`main`. API health must report that exact revision. Pre-deploy CI stays separate.
These health/API checks do not establish the authenticated upload, indexing, retrieval,
grounded-answer, school/class-isolation, or physical-cleanup journey. The required
Search Sphere release journey remains a separate open rollout phase. Optional exam
listing checks in this general diagnostics script are not a substitute for it.

## Answer deadline inventory before repair

Protected production run 42417055080 passed three fresh PDF uploads/indexes and
marker retrieval plus school/class isolation, then returned HTTP 502 on answer.
Sanitized Vercel logs confirm the consumer's HTTP read timed out. Search Sphere's
content-free telemetry shows embedding/reranking completed and hosted generation
completed about 2.5 seconds after ExamArena had already returned its timeout.
The client currently uses the same 30-second read timeout for answer generation
and metadata operations, and the service collapses upstream provider categories
into 502. These are partial upstream-failure/deadline contracts and are being
repaired independently of the also-failed cleanup verification. No input or
record contents were fetched for diagnosis.


Answer generation now has an independent `SEARCH_SPHERE_ANSWER_TIMEOUT_SECONDS`
(default 55 seconds, hard cap 55), including admission, transport and body reading.
An explicitly supplied client timeout can narrow it. Metadata/search keep the
existing timeout; there is one generation attempt and redirects remain disabled.
This aligns the consumer wait with the multi-stage backend response without
changing provider deadlines or sending a second inference request.

Answer failure responses preserve availability/rate-limit statuses 429/503/504;
other upstream integration failures remain 502. Messages are fixed server text.
`X-Search-Sphere-Error-Code` carries only allowlisted provider enums (or
`upstream_unavailable`), with no upstream diagnostics. Transport deadline expiry
returns 504/provider_timeout. Forty-six unit cases pass, including total-deadline
expiry, status/code mapping and private diagnostic suppression. The real PostgreSQL API/catalog/cleanup group has 47 passing distinct cases: 43
existing checks plus the updated timeout and three new status/code checks. The
old assertion expecting a timeout to be hidden as 502 was updated to require 504
and the safe timeout code. Black/Ruff and targeted client/config/exception mypy
pass. Service mypy still reports ten pre-existing Pydantic alias constructor errors.
