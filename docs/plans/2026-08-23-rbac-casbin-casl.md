# Role-Based Access Control (RBAC) with Casbin (Backend) & CASL (Frontend) Implementation Plan

> **For Claude / Agent:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement full, enterprise-grade Role-Based Access Control (RBAC) across both Frontend (using CASL) and Backend (using Casbin), ensuring strict policy enforcement, type safety, comprehensive test suites, and 0 regressions across all existing tests.

**Architecture:** 
- **Backend (FastAPI + Casbin):** Standardized Casbin RBAC engine (`app/core/rbac.py`) with a dedicated model configuration and policy definitions supporting `ADMIN`, `PRINCIPAL`, `TEACHER`, and `STUDENT` roles. Endpoints utilize `require_rbac_permission` dependencies and policy-based enforcement.
- **Frontend (Next.js + CASL):** Isomorphic authorization using `@casl/ability` and `@casl/react` (`src/lib/casl/`), providing an `AbilityProvider`, `useAbility()` hook, and `<Can />` component integrated into layout, sidebar, pages, and interactive UI elements.

**Tech Stack:** 
- Backend: Python 3.11, FastAPI, Casbin (`casbin>=1.35.0`), SQLAlchemy, Pytest
- Frontend: TypeScript, Next.js 16 (React 19), `@casl/ability`, `@casl/react`, Zustand, Vitest

---

## Permission Matrix

| Resource | Action | ADMIN | PRINCIPAL | TEACHER | STUDENT | Unauthenticated |
|---|---|:---:|:---:|:---:|:---:|:---:|
| `all` | `manage` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `school` | `create` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `school` | `read` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `school` | `update` / `delete` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `school` | `join` | ❌ | ❌ | ✅ | ❌ | ❌ |
| `school_classes` | `create` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `school_classes` | `read` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `school_classes` | `manage` (students/teacher) | ✅ | ✅ | ✅ (assigned) | ❌ | ❌ |
| `school_classes` | `join` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `exams` | `create` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `exams` | `read` / `search` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `exams` | `update` / `delete` | ✅ | ✅ | ✅ (creator) | ❌ | ❌ |
| `exams` | `publish` | ✅ | ✅ | ✅ (creator) | ❌ | ❌ |
| `questions` | `create` / `update` / `delete` | ✅ | ✅ | ✅ (creator) | ❌ | ❌ |
| `attempts` | `start` / `submit` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `attempts` | `read` | ✅ | ✅ | ✅ | ✅ (own) | ❌ |
| `attempts` | `proctoring_violation` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `join_requests` | `create` | ❌ | ❌ | ✅ (school) | ✅ (class) | ❌ |
| `join_requests` | `approve` / `reject` | ✅ | ✅ | ✅ (for class) | ❌ | ❌ |
| `audit` | `read` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `chat` / `profile` | `read` / `update` | ✅ | ✅ | ✅ | ✅ | ❌ |

---

## Tasks

### Task 1: Backend Casbin Core Engine Setup
**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/app/core/rbac_model.conf`
- Create: `backend/app/core/rbac.py`
- Create: `backend/tests/test_casbin_rbac.py`

**Steps:**
1. Add `casbin>=1.35.0` to `backend/requirements.txt` and install in Docker/venv.
2. Define Casbin RBAC configuration in `rbac_model.conf` and `rbac.py` with programmatic fallback/policy definitions.
3. Write `backend/tests/test_casbin_rbac.py` verifying all roles and actions against the policy matrix.
4. Run `pytest backend/tests/test_casbin_rbac.py` to confirm all assertions pass.

### Task 2: Backend Router & Dependency Integration
**Files:**
- Modify: `backend/app/api/deps.py`
- Modify: `backend/app/exams/router.py`
- Modify: `backend/app/exams/permissions.py`
- Modify: `backend/app/school/router.py`
- Modify: `backend/app/school_class/router.py`
- Modify: `backend/app/attempts/router.py`
- Modify: `backend/app/audit/router.py`
- Modify: `backend/app/join_requests/router.py`
- Modify: `backend/app/questions/router.py`
- Modify: `backend/app/sections/router.py`

**Steps:**
1. Export `require_rbac_permission(resource, action)` from `app/api/deps.py` and `app/core/rbac.py`.
2. Connect route endpoints and permission helpers to Casbin policy evaluation.
3. Run backend test suite (`docker compose exec backend pytest -v`) to ensure complete backwards compatibility and 0 failures.

### Task 3: Frontend CASL Ability & Context Setup
**Files:**
- Modify: `package.json` (already added `@casl/ability` & `@casl/react`)
- Create: `src/lib/casl/types.ts`
- Create: `src/lib/casl/ability.ts`
- Create: `src/lib/casl/AbilityContext.tsx`
- Create: `src/lib/casl/index.ts`
- Modify: `src/app/providers.tsx`
- Create: `src/__tests__/lib/casl.test.ts`

**Steps:**
1. Create strongly typed actions (`manage`, `create`, `read`, `update`, `delete`, `start`, `submit`, `join`, `approve`, `reject`) and subjects (`all`, `Exam`, `Question`, `Attempt`, `School`, `SchoolClass`, `Student`, `Teacher`, `Principal`, `JoinRequest`, `AuditLog`, `Profile`, `Chat`).
2. Implement `defineAbilityFor(user)` producing a CASL `PureAbility` / `MongoAbility`.
3. Create `AbilityProvider`, `useAbility()`, and `<Can />` context wrapper.
4. Add `<AbilityProvider>` to `src/app/providers.tsx`.
5. Write and execute Vitest unit tests in `src/__tests__/lib/casl.test.ts` to test all roles.

### Task 4: Frontend UI & Component CASL Integration
**Files:**
- Modify: `src/components/navbars/AppSidebar.tsx`
- Modify: `src/app/(protected)/(any-auth)/dashboard/page.tsx`
- Modify: `src/app/(protected)/(any-auth)/exams/[examId]/page.tsx`
- Modify: `src/components/exam/ExamCard.tsx`

**Steps:**
1. Integrate `useAbility()` and `<Can />` to conditionally render exam editing actions, management links, and role-restricted features.
2. Run TypeScript checks (`pnpm type-check`) and linting (`pnpm lint`).
3. Run full Vitest suite (`pnpm test:run`).

### Task 5: Final Validation Across Full Stack
**Steps:**
1. Run backend tests: `docker compose exec backend pytest -v`
2. Run frontend tests: `pnpm test:run`
3. Run frontend type checks: `pnpm type-check`
4. Run frontend lint: `pnpm lint`
5. Verify 0 errors, 0 regressions across the entire codebase.
