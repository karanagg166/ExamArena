# Tech Stack Blueprint - Exam Arena

This document defines the complete technology stack for Exam Arena, covering:
- what is actively used now,
- what is already present in the repo and can be activated,
- what is recommended for future scale.

## 1) Current Core Stack (Actively Used)

### Frontend
- Framework: Next.js 16 (App Router) + React 19 + TypeScript 5
- Styling/UI: Tailwind CSS v4, Radix UI primitives, custom UI layer
- State management: Zustand stores
- API client: Axios
- Validation/forms: React Hook Form + Zod
- Date handling: date-fns
- Icons/animation/charts: lucide-react, framer-motion, recharts
- Error monitoring: Sentry for Next.js

### Backend
- API framework: FastAPI (Python 3.11)
- App server: Uvicorn (ASGI)
- Data validation/settings: Pydantic v2 + pydantic-settings
- ORM/DB client: Prisma Client Python
- Authentication: JWT-based flow with role-based authorization
- Realtime: python-socketio (for websocket/event features)
- Error monitoring: sentry-sdk (FastAPI integration)

### Database and Data Model
- Database: PostgreSQL
- Schema and migrations: Prisma schema + migrations

### DevEx and Tooling
- Package manager: pnpm
- Lint/format/typecheck (frontend): ESLint, TypeScript
- Lint/format/typecheck (backend): Ruff, Black, MyPy
- Tests (frontend): Vitest, Testing Library, Playwright
- Tests (backend): Pytest, pytest-asyncio, httpx
- Containerization: Docker + Docker Compose

## 2) Present in Repo / Dependencies (Enable As Needed)

These are already listed in dependencies or configuration and can be turned on with minimal setup:
- Clerk (@clerk/nextjs) for managed auth flows
- Next themes (next-themes) for theme switching
- ARQ + Redis for background processing and queues
- boto3 for object storage integrations (S3-compatible)
- OpenAI + LangChain for AI-assisted workflows
- OpenCV + face_recognition for proctoring/computer-vision features
- Report/export stack: reportlab, pandas, openpyxl, xlsx, jspdf, jspdf-autotable

## 3) Target Future Stack (Recommended Roadmap)

### Platform and Architecture
- Keep Next.js + FastAPI + PostgreSQL + Prisma as the long-term base.
- Add clear service boundaries for:
  - exam authoring,
  - attempt/proctoring,
  - reporting/analytics,
  - AI evaluation.

### Infrastructure
- Background workers: standardize ARQ workers with Redis and dedicated queues.
- Object storage: formalize S3-compatible storage strategy (R2 or AWS S3) for uploads/reports.
- Caching: introduce Redis caching for heavy list and analytics endpoints.

### Observability
- Keep Sentry in FE/BE and add:
  - structured logs (loguru + request correlation ids),
  - basic metrics (latency, throughput, error rates),
  - health/readiness endpoints per service.

### Security and Auth
- Keep server-side role enforcement in FastAPI.
- Add:
  - refresh-token rotation,
  - rate limiting for auth and exam-attempt endpoints,
  - audit trails for exam edits and grading changes.

### Quality and Release
- Expand e2e coverage for critical journeys:
  - teacher creates exam,
  - student attempts exam,
  - principal/admin review workflows.
- CI pipeline targets:
  - lint + typecheck + unit tests on pull requests,
  - smoke tests against Docker Compose before merge.

## 4) Versioned Snapshot (As of 2026-04-02)

- Next: 16.1.6
- React / React DOM: 19.2.4
- TypeScript: 5.x
- Tailwind CSS: 4.x
- FastAPI: 0.110.0
- Uvicorn: 0.27.1
- Prisma Client Python: >=0.15.0
- date-fns: 4.1.0

## 5) Decision Summary

- Primary stack (keep): Next.js + FastAPI + Prisma + PostgreSQL.
- Near-term activation: Redis/ARQ workers, stronger observability, storage strategy.
- Future scale focus: queue-backed async workloads, auditability, and test depth for exam-critical flows.
