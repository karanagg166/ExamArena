# GitHub Copilot Instructions — Exam Arena

---

## 🧠 How Copilot Should Think — Task Execution Framework

Before writing any code, Copilot must follow this structured thinking process for every task.
Never jump straight to writing code. Always plan first.

### Step 1 — UNDERSTAND
Read the task carefully. Ask:
- What exactly is being asked?
- Which part of the system does this touch? (frontend / backend / both)
- Which role(s) are affected? (STUDENT / TEACHER / PRINCIPAL / ADMIN)
- Is this a new feature, a bug fix, a refactor, or a new module?

### Step 2 — EXPLORE
Before writing anything, explore the existing codebase:
- Read the relevant existing files in the same module
- Check `schema.prisma` for the exact model fields and relations
- Check existing `schemas.py` for patterns already used
- Check existing `router.py` and `crud.py` for naming conventions
- Check the existing TypeScript types in `@/types/`
- Check if a similar component already exists in `components/`

### Step 3 — PLAN
Write out a short plan as comments before writing code:
```
// Plan:
// 1. Create SchoolFilterParams schema in schemas.py
// 2. Add get_schools() crud function with dynamic where clause
// 3. Add GET /schools/ route with Query params
// 4. Create School type in @/types/school.ts
// 5. Create SchoolCard component
// 6. Create SchoolsPage with filters + debounce + local state
```
Never skip this step for tasks that touch more than one file.

### Step 4 — CHECK DEPENDENCIES
Before using any library or package:
- Verify it is already installed in `package.json` or `requirements.txt`
- Never suggest installing a new package without flagging it explicitly
- If a new package is needed, call it out clearly:
  ```
  // ⚠️ New dependency required: npm install socket.io-client
  ```

### Step 5 — BUILD
Write code file by file in this order:
1. **Types** (`@/types/`) or **Schemas** (`schemas.py`) first — establish the data shape
2. **Backend CRUD** (`crud.py`) — database operations
3. **Backend Router** (`router.py`) — expose the endpoints
4. **Frontend API call** — wire up the fetch
5. **UI Components** — card, list, form components
6. **Page** — assemble everything together

### Step 6 — REVIEW
After generating code, self-check:
- Does every new file follow the naming conventions?
- Are all TypeScript types properly imported from `@/types/`?
- Are all Prisma model names in snake_case in Python?
- Is there any business logic accidentally placed in a router?
- Are all loading, error, and empty states handled?
- Is any secret or credential accidentally hardcoded?

---

## 🗂️ Task Classification

When given a task, first classify it into one of these categories and follow the matching workflow:

### 🆕 New Module (e.g. "add exam results feature")
```
Workflow:
1. Read schema.prisma — identify the relevant models
2. Create schemas.py with Request, Response, FilterParams
3. Create crud.py with all DB operations
4. Create router.py and register in main.py
5. Create @/types/<module>.ts
6. Create components/<module>/<Module>Card.tsx
7. Create app/<role>/<module>/page.tsx
```

### 🔍 New Page with Filters (e.g. "filter and list teachers")
```
Workflow:
1. Identify all filterable fields from the type/schema
2. Define Filters type with all fields defaulting to ""
3. Build fetchData with URLSearchParams — strip empty values
4. Add 400ms debounce via useEffect + clearTimeout
5. Render: loading skeletons → error banner → empty state → grid of cards
6. Add FilterInput and FilterSelect sub-components at bottom of file
```

### 📄 New Detail Page (e.g. "show school details")
```
Workflow:
1. Get ID from useParams — never from window.location
2. Local useState for data, loading, error
3. useEffect calls fetch on mount
4. Render: Spinner → Error card → null guard → actual content
```

### 🔧 Bug Fix
```
Workflow:
1. Read the error message carefully — identify the exact file and line
2. Explore that file and related files before suggesting a fix
3. Explain WHY the bug happened before showing the fix
4. Show only the minimal change needed — never rewrite the whole file
```

### ♻️ Refactor
```
Workflow:
1. Read the existing code fully before suggesting changes
2. Identify what specifically is wrong (performance, readability, wrong pattern)
3. Refactor in the smallest steps possible
4. Never change behaviour — only structure
```

---

## 📖 Reading & Documentation Workflow

When Copilot needs to use an unfamiliar API, library, or feature:

1. **State what you are looking up** — e.g. "Checking Prisma's `include` syntax for nested relations"
2. **Reference the correct documentation source**:
   - Prisma Python → https://prisma-client-py.readthedocs.io
   - FastAPI → https://fastapi.tiangolo.com
   - Next.js App Router → https://nextjs.org/docs/app
   - Socket.IO Python → https://python-socketio.readthedocs.io
   - Pydantic v2 → https://docs.pydantic.dev/latest
   - Tailwind CSS → https://tailwindcss.com/docs
   - Zustand → https://docs.pmnd.rs/zustand
3. **Show the minimal relevant snippet** from the docs
4. **Apply it to the project's pattern** — never copy-paste docs examples directly

---

## 🏗️ New Feature Planning Template

When asked to build a complete new feature, always output this plan first before any code:

```
## Feature: <Feature Name>

### What it does
<one sentence description>

### Files to create
Backend:
- [ ] app/<module>/schemas.py
- [ ] app/<module>/crud.py
- [ ] app/<module>/router.py

Frontend:
- [ ] @/types/<module>.ts
- [ ] @/components/<module>/<Module>Card.tsx
- [ ] @/app/<role>/<module>/page.tsx

### Schema changes needed
- [ ] None / or list the prisma model changes

### New dependencies needed
- [ ] None / or list with install commands

### API endpoints
- GET    /api/v1/<module>/        — list with filters
- GET    /api/v1/<module>/{id}    — single item
- POST   /api/v1/<module>/        — create
- PATCH  /api/v1/<module>/{id}    — update
- DELETE /api/v1/<module>/{id}    — delete

### Roles that can access
- [ ] ADMIN
- [ ] PRINCIPAL
- [ ] TEACHER
- [ ] STUDENT
```

Only after showing this plan, proceed to write the code file by file.

---

## 📁 File Creation Order

Always create files in this strict order — never create a page before its dependencies exist:

```
1. schema.prisma changes (if needed)
2. prisma migrate dev
3. Backend schemas.py
4. Backend crud.py
5. Backend router.py
6. Register router in main.py
7. Frontend @/types/<module>.ts
8. Frontend component (Card, Form etc)
9. Frontend page
```

---

## 💬 Comment Style

Use structured comments to make intent clear:

```tsx
// ── Section headers ───────────────────────────────────────────────────────
// Use this for major sections inside a file

// ✅ Use this to mark correct patterns

// ❌ Use this to mark patterns to avoid

// ⚠️ Use this for warnings (new dependency, breaking change, env var needed)

// TODO: Use this for known follow-up work

// NOTE: Use this for non-obvious decisions that need explanation
```

---

## 🔍 Before Suggesting Any Code — Checklist

Copilot must mentally run through this checklist before every suggestion:

```
□ Have I read the existing files in this module?
□ Have I checked schema.prisma for exact field names?
□ Am I using snake_case for all Prisma Python model names?
□ Are all TypeScript types imported from @/types/ not defined inline?
□ Is business logic in crud.py and NOT in router.py?
□ Have I handled loading, error, and empty states?
□ Is useCallback used for functions in dependency arrays?
□ Am I using useParams not window.location?
□ Am I using api.get not raw fetch?
□ Are there any hardcoded secrets or credentials?
□ Does every useEffect have a cleanup return?
□ Is the debounce (400ms) in place for filter inputs?
```

---

## 🧩 Component Design Rules

When designing a new component, follow this thinking process:

1. **What data does it need?** → Define the props interface first
2. **Is it reusable or page-specific?**
   - Reusable across modules → `components/ui/`
   - Domain-specific → `components/<domain>/`
   - Used only in one page → define as a sub-component at the bottom of the page file
3. **Does it need state?** → If not, make it a pure function component with no hooks
4. **Does it navigate?** → Accept an optional `onClick` prop rather than hardcoding `router.push`
5. **Does it show data that could be null/undefined?** → Always use `|| "—"` or `?? "—"` fallback

---

## 🔐 Auth & Role Guard Rules

Every protected page must:

1. Check `current_user` via `Depends(get_current_user)` on the backend route
2. Check the user's role before returning data:

```python
# ✅ Correct role check in router
@router.get("/admin/schools")
async def get_all_schools(current_user=Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Access denied")
    return await fetch_schools()
```

3. On the frontend, never rely only on UI hiding — always validate on backend too
4. Role-based redirects happen in `middleware.ts` or in the page's `useEffect`

---

## ⚡ Performance Rules

### Frontend
- Use `useCallback` for any function passed as a prop or used in a `useEffect` dep array
- Use `useMemo` only for genuinely expensive computations (filtering 1000+ items)
- Never use `useMemo` or `useCallback` for simple values or one-liner functions
- Debounce all filter/search inputs by 400ms
- Use skeleton loaders — never show a blank screen while loading
- Prefer server-side filtering over client-side filtering for large datasets

### Backend
- Never make queries inside loops — always use `include` in Prisma
- Use `find_unique` for ID lookups, `find_first` for single-condition lookups
- Use `find_many` with `where` for filtered lists
- Add `@@index` for any field used frequently in `where` clauses
- Use `select` to limit returned fields when you don't need the full model

---

## 🐛 Error Handling Standards

### Frontend errors
```tsx
// Always use this exact error extraction pattern
setError(err?.response?.data?.detail ?? err.message ?? "Something went wrong");
```

### Backend errors
```python
# 400 — bad input
raise HTTPException(status_code=400, detail="Invalid school code format")

# 401 — not authenticated
raise HTTPException(status_code=401, detail="Not authenticated")

# 403 — authenticated but wrong role
raise HTTPException(status_code=403, detail="Access denied")

# 404 — resource not found
raise HTTPException(status_code=404, detail="School not found")

# 409 — conflict (duplicate)
raise HTTPException(status_code=409, detail="School code already exists")
```

---

## 🧪 Testing Mindset

When generating code, always think about edge cases:
- What if the API returns an empty array?
- What if a required relation is null? (`teacherId` is optional on `SchoolClass`)
- What if the user navigates to a detail page with an invalid ID?
- What if the filter returns 0 results?
- What if two users create the same `schoolCode` simultaneously?

Always handle these cases explicitly — never assume the happy path only.

---

## Project Overview
Exam Arena is a full-stack school management and examination platform.
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Zustand, Axios
- **Backend**: Python, FastAPI, Prisma (prisma-client-py), PostgreSQL (Neon), Docker
- **Auth**: JWT-based authentication with role-based access control
- **Realtime**: Socket.IO (python-socketio on backend, socket.io-client on frontend)

---

## Roles
Users can have one of these roles: `STUDENT`, `TEACHER`, `PRINCIPAL`, `ADMIN`
Always consider role-based access when generating route guards, API endpoints, or UI components.

---

## Project Structure

### Frontend (`/frontend`)
```
app/                   # Next.js App Router pages
  (auth)/              # Auth pages — login, register
  principal/           # Principal dashboard and pages
  teacher/             # Teacher dashboard and pages
  student/             # Student dashboard and pages
  admin/               # Admin dashboard and pages
components/
  ui/                  # Reusable base UI components (Button, Card, Spinner etc)
  school/              # School-specific components (SchoolCard, SchoolClassCard)
  teacher/             # Teacher-specific components (TeacherCard)
hooks/                 # Custom React hooks (useSocket etc)
lib/
  axios.ts             # Axios instance with base URL and interceptors
  socket.ts            # Socket.IO singleton
stores/                # Zustand stores — only for global shared state
types/                 # TypeScript types — one file per domain
  school.ts
  teacher.ts
  schoolClass.ts
```

### Backend (`/backend`)
```
app/
  auth/                # JWT auth — router, crud, dependencies, schemas
  school/              # School — router, crud, schemas
  schoolClass/         # SchoolClass — router, crud, schemas
  teacher/             # Teacher — router, crud, schemas
  student/             # Student — router, crud, schemas
  exam/                # Exam — router, crud, schemas
  socket.py            # Socket.IO server instance
  db.py                # Prisma client connection
  main.py              # FastAPI app entry point
prisma/
  schema.prisma        # Single source of truth for all models
```

---

## Frontend Rules

### Components
- All components are functional — never use class components
- Always use `'use client'` directive for components that use hooks or browser APIs
- Component files use PascalCase: `SchoolCard.tsx`, `TeacherCard.tsx`
- One component per file
- Props interface defined directly above the component

```tsx
// ✅ Correct pattern
interface SchoolCardProps {
  school: School;
  onClick?: (school: School) => void;
}

export default function SchoolCard({ school, onClick }: SchoolCardProps) {}
```

### Data Fetching
- **Never use Zustand for server/list data** — use local `useState` + `useEffect`
- Zustand is only for global state: `currentUser`, `auth token`, `theme`
- Always debounce filter inputs by 400ms before calling the API
- Always handle three states: `loading`, `error`, `empty`
- Use `err?.response?.data?.detail ?? err.message ?? "Something went wrong"` for error messages

```tsx
// ✅ Correct data fetching pattern
const [data, setData] = useState<School[]>([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

useEffect(() => {
  const timeout = setTimeout(() => fetchData(filters), 400);
  return () => clearTimeout(timeout);
}, [filters]);
```

### Hooks
- `useCallback` for functions that are in dependency arrays or passed as props
- `useMemo` for expensive computations only — not for simple values
- `useParams<{ id: string }>()` for getting URL params — never use `window.location`
- Always clean up event listeners and timeouts in `useEffect` return

### TypeScript
- Always type component props explicitly — never use `any` for props
- Use `import type` for type-only imports
- Types live in `@/types/` — never define types inside page or component files
- Use optional chaining `?.` and nullish coalescing `??` over `&&` and `||` for nullable values

### API Calls
- All API calls go through `@/lib/axios` — never use raw `fetch`
- Always use TypeScript generics: `api.get<School[]>(url)`
- Build query strings with `URLSearchParams` — filter out empty values before sending
- API base URL comes from `NEXT_PUBLIC_BACKEND_URL` env variable

```tsx
// ✅ Correct API call pattern
const query = new URLSearchParams(
  Object.fromEntries(Object.entries(params).filter(([_, v]) => v !== ""))
).toString();
const { data } = await api.get<School[]>(`/api/v1/schools${query ? `?${query}` : ""}`);
```

### Routing
- Use `useParams` from `next/navigation` — not `useRouter().query`
- Use `useRouter().push()` for programmatic navigation
- Dynamic routes follow: `app/[schoolId]/classes/[classId]/page.tsx`

### Tailwind
- Use Tailwind utility classes only — no inline styles
- Responsive classes: `sm:` `md:` `lg:` `xl:`
- Hover/focus states: `hover:` `focus:` `group-hover:`
- Dark variants use `dark:` prefix
- Prefer `gap-` over `margin` for spacing inside flex/grid containers
- Common layout: `flex items-center justify-between`, `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5`

---

## Backend Rules

### File Structure per module
Every module (school, teacher, exam etc) must have exactly:
```
router.py    # FastAPI route definitions only — no business logic
crud.py      # All database operations using Prisma
schemas.py   # Pydantic request/response models
```

### Schemas
Each module should have separate schemas for each concern:

```python
# ✅ Correct schema separation
class SchoolCreateRequest(BaseModel): ...   # incoming POST body
class SchoolUpdateRequest(BaseModel): ...   # incoming PATCH body
class SchoolFilterParams(BaseModel): ...    # query param filters
class SchoolResponse(BaseModel): ...        # outgoing response shape
```

- Always set `model_config = {"from_attributes": True}` on response schemas
- Use `Optional[str] = None` not `str | None` for broader Python version compatibility
- Use `EmailStr` from pydantic for email fields
- Enums must extend both `str` and `Enum`: `class SchoolType(str, Enum)`

### Routers
- Routers only call crud functions — zero business logic or DB calls in router
- Always use `Depends(get_current_user)` on protected routes
- Always use `Query(None)` for optional query params
- Raise `HTTPException(status_code=404, detail="X not found")` for missing resources
- Return types always declared: `response_model=list[SchoolResponse]`

```python
# ✅ Correct router pattern
@router.get("/{school_id}", response_model=SchoolResponse)
async def fetch_school(
    school_id: str,
    current_user=Depends(get_current_user),
):
    school = await get_school_by_id(school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return school
```

### CRUD
- All DB operations use `db.prisma.<model_name>` (snake_case)
- `SchoolClass` model → `db.prisma.school_class` (Python Prisma is always snake_case)
- Build `where` dict dynamically — only add keys that have values
- Use `{"contains": value, "mode": "insensitive"}` for case-insensitive text search
- Use `{"gte": min, "lte": max}` for numeric range filters
- Always use `include` for relations — never make separate queries in a loop (N+1)

```python
# ✅ Correct where clause pattern
where = {}
if name:        where["name"]  = {"contains": name, "mode": "insensitive"}
if city:        where["city"]  = {"contains": city, "mode": "insensitive"}
if school_type: where["type"]  = school_type  # exact match for enums

results = await db.prisma.school.find_many(where=where)
```

### Naming conventions
- Route files: `router.py`, `crud.py`, `schemas.py`
- Functions: `get_school_by_id`, `create_school`, `update_school`, `delete_school`
- Never use `class` as a variable name — use `school_class` instead

---

## Prisma Schema Rules
- `schema.prisma` is the single source of truth — never hardcode field names elsewhere
- All IDs use `@id @default(cuid())`
- All models have `createdAt DateTime @default(now())` and `updatedAt DateTime @updatedAt`
- Cascade deletes: `onDelete: Cascade` for required relations, `onDelete: SetNull` for optional
- Always add `@@index` for foreign key fields
- Optional relations use `?` — `schoolId String?`
- After any schema change always run: `prisma migrate dev --name <description>`

---

## Prisma Model → Python Client Name Mapping
| Schema model       | Python client access          |
|--------------------|-------------------------------|
| `School`           | `db.prisma.school`            |
| `SchoolClass`      | `db.prisma.school_class`      |
| `Teacher`          | `db.prisma.teacher`           |
| `Student`          | `db.prisma.student`           |
| `TeacherClass`     | `db.prisma.teacher_class`     |
| `StudentExam`      | `db.prisma.student_exam`      |
| `StudentExamAnswer`| `db.prisma.student_exam_answer`|

---

## Environment Variables

### Frontend `.env.local`
```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### Backend `.env`
```
DATABASE_URL=postgresql://...
JWT_SECRET=...
FRONTEND_URL=http://localhost:3000
```

---

## Docker
- Backend runs on port `8000`
- Frontend runs on port `3000`
- Services are named `exam_arena_backend` and `exam_arena_frontend`
- Always use `env_file: - .env` in docker-compose to load environment variables
- Prisma generate runs on container startup before uvicorn

---

## Socket.IO
- Socket server is mounted at `/ws` in FastAPI
- Frontend connects via `path: "/ws/socket.io"`
- Socket instance is a singleton in `@/lib/socket.ts`
- Use `useSocket` hook to connect in components
- Always clean up socket listeners on component unmount: `socket.off("event")`
- Use rooms for scoped events: `school-{schoolId}`, `class-{classId}`

---

## ❌ Do Nots
- ❌ Never define types inside page or component files
- ❌ Never use `window.location` for routing or params
- ❌ Never store list/server data in Zustand
- ❌ Never put business logic in routers
- ❌ Never make N+1 database queries — always use `include`
- ❌ Never use `db.prisma.schoolClass` — it's `db.prisma.school_class`
- ❌ Never expose raw passwords or secrets in code or chat
- ❌ Never use `any` type in TypeScript unless absolutely unavoidable
- ❌ Never use `useEffect` with an async function directly — define async inside
- ❌ Never commit `.env` files — always add to `.gitignore`
- ❌ Never skip the planning step for multi-file tasks
- ❌ Never suggest a new npm/pip package without flagging it with ⚠️
- ❌ Never write a page before its type and component dependencies exist
- ❌ Never hardcode role checks in the frontend only — always enforce on backend too
- ❌ Never copy-paste documentation examples directly — always adapt to project patterns