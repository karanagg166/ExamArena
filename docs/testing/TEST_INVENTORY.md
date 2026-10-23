# ExamArena Test Inventory & Quality Verification Matrix

> **Project**: ExamArena (`https://github.com/karanagg166/ExamArena`)  
> **Production URL**: `https://exam-arena-mu.vercel.app`  
> **Architecture**: Next.js 14 (App Router) + FastAPI (Serverless Python via `/api/index.py`) + PostgreSQL + Redis + ARQ Worker  
> **Verified Baseline**: 665 Backend Tests (663 Passed, 2 Skipped, 0 Failed) + 38 Frontend Vitest Suites

---

## 1. Architecture & Testing Topology

ExamArena is deployed as a hybrid serverless system on Vercel:
- **Frontend**: Next.js 14 App Router (`src/app/`) handling SSR, client interactions, exam taking interface, and proctoring UI.
- **Backend**: FastAPI ASGI application (`backend/app/main.py`) routed via Vercel Serverless rewrite (`/api/index.py`).
- **Database**: PostgreSQL with SQLAlchemy 2.0 async engine and connection pooling.
- **Cache & Message Broker**: Redis for token blacklisting, live presence tracking, draft revisions, and ARQ queue tasks.
- **Background Worker**: ARQ worker processing async bulk grading, PDF/JSON question extraction, and answer key imports.

---

## 2. Test Execution Inventory by Level

### Level 1: Unit Tests (`backend/tests/unit/`, `backend/tests/core/`)
Pure logic, input parsing, cryptography, schema validation, and state machines with deterministic isolation.

| Feature Area | Source Module | Test File | Test Count | Key Invariants Verified |
| :--- | :--- | :--- | :---: | :--- |
| **Authentication & Tokens** | `app.core.security` | `unit/test_security.py` | 18 | Password hashing with bcrypt, JWT creation, claims validation (`sub`, `jti`, `exp`), token expiry parsing, backward compatibility. |
| **Casbin RBAC Engine** | `app.core.casbin` | `test_casbin_rbac.py` | 12 | Principal, Teacher, Student, Admin permissions; cross-school access denial; policy enforcement. |
| **Answer Key Parser** | `app.imports.answer_key` | `unit/test_answer_key_parser.py` | 15 | Parsing CSV/JSON formats, fuzzy question matching, option normalization, deterministic deduplication. |
| **Score Normalization** | `app.analytics.service` | `unit/test_analytics.py` | 14 | Percentage calculation, ties ordering, zero-denominator safeguards, weighted section scoring. |
| **Draft Versioning** | `app.attempts.crud` | `unit/test_attempt_drafts.py` | 8 | Base revision concurrency detection, monotonic sequence numbers, optimistic locking conflict resolution. |
| **Socket Room Scoping** | `app.sockets.manager` | `unit/test_sockets.py` | 14 | Room ID partitioning (`school:{id}`, `exam:{id}`), dead socket pruning, event envelope structure. |
| **Worker Topology & Config**| `app.imports.worker` | `unit/test_worker_topology.py` | 12 | Health check interval, queue naming, job registration, Redis pool connection settings. |
| **Health & Readiness Probes**| `app.main` | `unit/test_health_probes.py` | 3 | Liveness `/health` (200 OK + `git_commit`), readiness `/ready` (bounded `SELECT 1`), failure on database down. |
| **Grading Redaction** | `app.attempts.schemas` | `unit/test_student_grading_redaction.py` | 6 | Redaction of AI proposals, solution keys, and explanations before official results release. |

---

### Level 2: Component & Frontend Tests (`src/__tests__/`)
React component rendering, user interactions, input forms, and client state machines.

| Component Group | Component File | Test Suite | Coverage Focus |
| :--- | :--- | :--- | :--- |
| **Exam Taking Interface** | `components/exam/ExamPlayer.tsx` | `ExamPlayer.test.tsx` | Question navigation, autosave indicator, timer countdown, option selection, submit confirmation dialog. |
| **Answer Key Importer** | `components/teacher/AnswerKeyModal.tsx` | `AnswerKeyModal.test.tsx` | File drag-and-drop, CSV validation errors, field mapping preview, import trigger. |
| **Analytics Dashboard** | `components/dashboard/AnalyticsOverview.tsx`| `Analytics.test.tsx` | Role-based widgets, school metrics display, empty state handling, student performance graphs. |
| **Live Proctoring Feed** | `components/proctor/ProctorFeed.tsx` | `ProctorFeed.test.tsx` | Real-time presence indicators, focus-lost warning pills, socket reconnection banners. |

---

### Level 3: API & Endpoint Tests (`backend/tests/api/`, `backend/tests/exams/`, `backend/tests/attempts/`)
FastAPI route validation, payload deserialization, HTTP status codes, and error formatting.

| API Domain | Route Prefix | Test File | Verified Endpoints & Behaviors |
| :--- | :--- | :--- | :--- |
| **Exams Management** | `/api/v1/exams` | `exams/test_exams.py` | `POST /`, `GET /`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`: validation, ownership check, section embedding. |
| **Sections & Questions** | `/api/v1/exams/{id}/sections` | `sections/test_sections.py` | Section creation, re-ordering, question attachment, point balance invariants. |
| **Student Attempts** | `/api/v1/attempts` | `attempts/test_attempts.py` | `POST /start`, `GET /{id}`, `POST /{id}/submit`: attempt eligibility, time limit enforcement, deadline lock. |
| **School Management** | `/api/v1/schools` | `api/test_api_school.py` | Public school listing, creation restricted to SuperAdmin/Principal, unauthenticated 401. |
| **Bulk AI Grading** | `/api/v1/exams/{id}/grade` | `api/test_bulk_grading.py` | Triggering async batch grading, summary counts, grade preservation for manually reviewed items. |
| **Course Materials** | `/api/v1/materials` | `api/test_course_materials_api.py` | RAG context retrieval, student question answering, cross-school data isolation. |

---

### Level 4: Feature & Integration Tests (`backend/tests/integration/`)
Multi-module database flows, Redis caching, worker task scheduling, and end-to-end business rules.

| Feature Flow | Test File | Verified Invariants |
| :--- | :--- | :--- |
| **Golden Lifecycle Flow** | `integration/test_golden_lifecycle.py` | Teacher creates school -> creates exam -> student registers -> student takes exam -> autosaves drafts -> submits -> teacher grades -> results released -> analytics updated. |
| **Import Dispatch Policy** | `integration/test_import_dispatch_policy.py` | Worker health diagnostics; dispatch routes to ARQ when worker active; safe sync fallback when worker offline. |
| **Worker Queue Lifecycle** | `integration/test_worker_queue_lifecycle.py` | Redis queue cleanup, task retry limits, failure handling, worker heartbeat persistence. |
| **Anti-Cheating Token Revocation** | `integration/test_bug6_token_blacklist.py` | Password change or logout invalidates existing `jti` in Redis; rejected on all protected routes. |
| **Audit Trail Lifecycle** | `integration/test_audit_trail.py` | Login attempts, grade overrides, role changes recorded in `audit_logs` with actor and timestamp. |
| **Deterministic Tie-Breaking** | `analytics/test_analytics.py` | Class rank calculations order deterministic ties by submission time rather than arbitrary DB row order. |

---

### Level 5: Security & IDOR Authorization Tests (`backend/tests/analytics/test_analytics_rbac_idor.py`, `backend/tests/api/`)
Cross-tenant, cross-school, and horizontal privilege escalation prevention.

| Security Assertion | Test Case | Target Invariant |
| :--- | :--- | :--- |
| **Cross-School Exam Isolation** | `test_cross_school_answer_isolation` | Students/teachers in School A cannot access or submit answers to exams in School B (HTTP 403/404). |
| **Student IDOR Protection** | `test_student_cannot_view_other_student_results_idor` | Student cannot inspect another student's attempt results via URL tampering. |
| **Teacher Unowned Exam IDOR**| `test_teacher_cannot_access_unowned_exam_analytics_idor` | Teacher cannot access performance analytics for exams created by teachers outside their department/school. |
| **AI Proposal Leak Defense** | `test_student_response_never_leaks_ai_proposal` | Students can never view AI grading suggestions or raw evaluation criteria in API payloads. |

---

## 3. CI Pipeline Status

- **Workflow File**: `.github/workflows/ci.yml`
- **Executed Checks**:
  1. Backend Linting (`ruff check`)
  2. Backend Unit & Integration Tests (`pytest backend/tests`)
  3. Frontend Lint & Build (`pnpm lint`, `pnpm build`)
- **Verified Run**: All 665 backend test cases pass cleanly in 7m 8s.
