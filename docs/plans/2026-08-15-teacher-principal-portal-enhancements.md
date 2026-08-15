# Teacher & Principal Portals, Exam Validation, Class Hierarchy & Results — Implementation Plan v2

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove school search from teacher student search; implement granular exam creation validation with past-date support and synchronized max marks; provide complete student exam results & chat oversight for teachers/principals; enforce Principal-as-Teacher hierarchy with class/teacher assignment; introduce teacher class join request approvals; and update the browser tab icon.

---

## Architecture Overview

### Key Codebase Facts (verified by code analysis)

1. **Layout guards are passthroughs:** `(teacher-only)/layout.tsx`, `(principal-only)/layout.tsx`, and `(staff-only)/layout.tsx` all render `<>{children}</>`. Role isolation and navigation are handled by the **sidebar** (`AppSidebar.tsx`) and by **backend RBAC** on each API endpoint.

2. **Principal navigation already includes Teacher routes:** `navItemsByRole.PRINCIPAL` in `AppSidebar.tsx` includes `/teacher/exams/create` and `/teacher/exams`.

3. **`get_teacher_from_user()` already resolves for Principals:** A Principal's `User` record has a corresponding `Teacher` record (`Principal.teacherId -> Teacher.id` where `Teacher.userId == Principal's User.id`). We will unify this into `get_current_staff_teacher(user)` so authorization checks are consistent across all exam and class management endpoints.

4. **Messaging Stack:** The project utilizes **Stream Chat** for direct messaging and conversations. Real-time updates for notifications/requests will leverage REST polling with Stream Chat integration.

5. **Backend Error Propagation:** `backend/app/exams/router.py:create_new_exam` currently catches all generic exceptions and raises a 500 error. We will update error handling to return specific 422 / 400 validation details directly to the frontend.

6. **Validation Engine:** `src/app/(protected)/(teacher-only)/teacher/exams/create/page.tsx` will be backed by a centralized `src/lib/exam-validation.ts` module with explicit error messages for empty questions, empty options, invalid sections, and option count constraints.

7. **Synchronized Marks:** `maxMarks` is dynamically computed on the frontend via `useMemo` from question marks and strictly re-computed/enforced on the backend inside `create_exam` and `update_exam` (`maxMarks = sum(q.marks for q in questions)`).

8. **School Scoping:** Scoping is enforced server-side via `StudentFilterParams.scopeSchoolId`. The `schoolName` and `schoolCode` search inputs on `(staff-only)/students/page.tsx` are redundant for staff and will be cleanly removed.

---

## Task 1: Remove School Filter from Staff Student Search

**Goal:** Remove `schoolName` and `schoolCode` search inputs from the staff student search page since teachers and principals are already scoped to their school by the backend.

**Files:**
- Modify: `src/app/(protected)/(staff-only)/students/page.tsx`
- Test: `src/__tests__/components/student/StudentsFilter.test.tsx`

### Step 1: Write the frontend unit test
Create `src/__tests__/components/student/StudentsFilter.test.tsx`:
```typescript
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import StudentsPage from "@/app/(protected)/(staff-only)/students/page";

vi.mock("@/lib/axios", () => ({
  api: { get: vi.fn().mockResolvedValue({ data: [] }) },
}));

describe("StudentsPage Filter UI", () => {
  it("renders personal and class filters but NOT school filters", () => {
    render(<StudentsPage />);
    expect(screen.getByLabelText(/Name/i)).toBeDefined();
    expect(screen.getByLabelText(/Email/i)).toBeDefined();
    expect(screen.getByLabelText(/Roll Number/i)).toBeDefined();
    expect(screen.getByLabelText(/Class Year/i)).toBeDefined();
    expect(screen.getByLabelText(/Section/i)).toBeDefined();
    expect(screen.queryByLabelText(/School Name/i)).toBeNull();
    expect(screen.queryByLabelText(/School Code/i)).toBeNull();
  });
});
```

### Step 2: Run test to verify failure
```bash
pnpm test run src/__tests__/components/student/StudentsFilter.test.tsx
```

### Step 3: Modify `students/page.tsx`
1. Update `Filters` type and `INITIAL_FILTERS` in `src/app/(protected)/(staff-only)/students/page.tsx` to remove `schoolName` and `schoolCode`.
2. Remove `<FilterInput id="filter-schoolname" ... />` and `<FilterInput id="filter-schoolcode" ... />`.

### Step 4: Run test to verify it passes
```bash
pnpm test run src/__tests__/components/student/StudentsFilter.test.tsx
```

---

## Task 2: Exam Creation Validation, Past Schedule Support & Auto Max Marks

**Goal:** Provide granular feedback for empty questions/options, permit exam `scheduledAt` to be in the past, and synchronize `maxMarks = sum(questions.marks)`.

**Files:**
- Create: `src/lib/exam-validation.ts`
- Modify: `src/app/(protected)/(teacher-only)/teacher/exams/create/page.tsx`
- Modify: `src/app/(protected)/(teacher-only)/teacher/exams/[examId]/edit/page.tsx`
- Modify: `backend/app/questions/schemas.py`
- Modify: `backend/app/exams/router.py`
- Modify: `backend/app/exams/crud.py`
- Test: `src/__tests__/lib/exam-validation.test.ts`
- Test: `backend/tests/exams/test_exam_validation.py`

### Step 1: Write failing unit tests

**Frontend test (`src/__tests__/lib/exam-validation.test.ts`):**
- Test rejection of empty exam title, empty description, missing `scheduledAt`.
- Test acceptance of past `scheduledAt` (valid date).
- Test rejection of `duration < 5`.
- Test rejection of empty questions list.
- Test rejection of empty question prompt text with specific message: `"Question 1 in Section A cannot be empty"`.
- Test rejection of empty option text: `"Option 1 for Question 1 in Section A cannot be empty"`.
- Test rejection of Multiple Choice question without at least one correct option.
- Test rejection of True/False question with != 2 options.
- Test auto-calculation of `maxMarks` via `computeMaxMarks`.

**Backend test (`backend/tests/exams/test_exam_validation.py`):**
- Test `QuestionBase` raises `ValidationError` on empty/whitespace `text`.
- Test `QuestionOptionBase` raises `ValidationError` on empty/whitespace `text`.
- Test `create_exam` sets `maxMarks = sum(q.marks)` regardless of input value.

### Step 2: Run tests to verify failure
```bash
pnpm test run src/__tests__/lib/exam-validation.test.ts
pytest backend/tests/exams/test_exam_validation.py
```

### Step 3: Implement validation & auto-synchronization

1. **`src/lib/exam-validation.ts`**:
   ```typescript
   import type { ExamCreate } from "@/types";

   const SECTION_PATTERN = /^Section [A-Z]$/;

   export function validateExam(exam: Partial<ExamCreate>): string | null {
     if (!exam.name?.trim()) return "Exam title is required.";
     if (!exam.description?.trim()) return "Description is required.";
     if (!exam.scheduledAt) return "Scheduled date and time is required.";
     if ((exam.duration ?? 0) < 5) return "Duration must be at least 5 minutes.";
     if (!exam.questions || exam.questions.length === 0) return "Add at least one question.";

     for (let i = 0; i < exam.questions.length; i++) {
       const q = exam.questions[i];
       const qNum = q.questionNumber ?? i + 1;
       const sec = q.section?.trim() || "Section A";

       if (!q.text?.trim()) {
         return `Question ${qNum} in ${sec} cannot be empty. Please enter question prompt.`;
       }
       if (!SECTION_PATTERN.test(sec)) {
         return `Invalid section "${sec}" for Question ${qNum}. Must be "Section A", "Section B", etc.`;
       }
       if (!q.marks || q.marks < 1) {
         return `Question ${qNum} in ${sec} must have marks greater than 0.`;
       }

       const needsOptions =
         q.questionType === "MULTIPLE_CHOICE" ||
         q.questionType === "TRUE_FALSE" ||
         q.questionType === "MULTIPLE_SELECT";

       if (needsOptions) {
         if (!q.options || q.options.length === 0) {
           return `Question ${qNum} in ${sec} must have options.`;
         }
         if (q.questionType === "TRUE_FALSE" && q.options.length !== 2) {
           return `Question ${qNum} in ${sec} (True/False) must have exactly 2 options.`;
         }
         for (let j = 0; j < q.options.length; j++) {
           if (!q.options[j].text?.trim()) {
             return `Option ${j + 1} for Question ${qNum} in ${sec} cannot be empty.`;
           }
         }
         if (!q.options.some((o) => o.isCorrect)) {
           return `Question ${qNum} in ${sec} must have at least one correct option selected.`;
         }
       }
     }
     return null;
   }

   export function computeMaxMarks(questions: { marks?: number }[]): number {
     return questions.reduce((sum, q) => sum + (q.marks ?? 0), 0);
   }
   ```

2. **`backend/app/questions/schemas.py`**:
   Add `@field_validator("text")` to `QuestionBase` and `QuestionOptionBase` to ensure stripped string is not empty.

3. **`backend/app/exams/router.py`**:
   Catch `ValueError` and `ValidationError` and raise HTTP 422 with exact detail messages instead of generic 500.

4. **`backend/app/exams/crud.py`**:
   Enforce `exam_obj.maxMarks = sum(q.marks for q in questions_list)` when creating or updating exams.

### Step 4: Run tests to verify they pass
```bash
pnpm test run src/__tests__/lib/exam-validation.test.ts
pytest backend/tests/exams/test_exam_validation.py
```

---

## Task 3: Student Academic & Exam Results History on Staff Student Detail Page

**Goal:** Enable teachers and principals to view all exam performance records, marks obtained, max marks, percentages, and status for any student in their school, along with direct chat access. Add an exam leaderboard results page.

**Files:**
- Modify: `backend/app/students/router.py` (add `GET /api/v1/students/{student_id}/exams`)
- Modify: `backend/app/attempts/crud.py` (add `get_student_exam_history`)
- Modify: `backend/app/attempts/schemas.py` (add `StudentExamHistoryItem`)
- Modify: `backend/app/exams/router.py` (add `GET /api/v1/exams/{exam_id}/results`)
- Modify: `backend/app/exams/crud.py` (add `get_exam_results`)
- Modify: `src/app/(protected)/(staff-only)/students/[studentId]/page.tsx`
- Modify: `src/app/(protected)/(teacher-only)/teacher/exams/[examId]/results/page.tsx`
- Test: `backend/tests/students/test_student_exam_history.py`
- Test: `src/__tests__/components/student/StudentExamHistory.test.tsx`

### Step 1: Write failing tests

**Backend test (`backend/tests/students/test_student_exam_history.py`):**
- Verify `GET /api/v1/students/{student_id}/exams` returns all student attempts with score details.
- Verify teachers/principals can access students in their school and get 403 for other schools.
- Verify `GET /api/v1/exams/{exam_id}/results` returns student ranking and scores.

**Frontend test (`src/__tests__/components/student/StudentExamHistory.test.tsx`):**
- Verify tab switching between "Profile Details", "Exam Results", and "Chat".
- Verify rendering of exam attempts table with marks obtained, max marks, and percentages.

### Step 2: Implement Backend Endpoints

1. **`StudentExamHistoryItem` schema** in `backend/app/attempts/schemas.py`:
   - `id`, `examId`, `examTitle`, `examCode`, `subject`, `examType`, `scheduledAt`, `submittedAt`, `status`, `marksObtained`, `maxMarks`, `percentage`, `isResultsReleased`.

2. **`get_student_exam_history`** in `backend/app/attempts/crud.py`:
   - Query `StudentExam` by `studentId` with eager loaded `Exam`. Compute `percentage = (marksObtained / maxMarks) * 100`.

3. **`GET /api/v1/students/{student_id}/exams`** in `backend/app/students/router.py`:
   - Authorize staff members from the student's school. Return `list[StudentExamHistoryItem]`.

4. **`GET /api/v1/exams/{exam_id}/results`** in `backend/app/exams/router.py`:
   - Query attempts for `exam_id` ordered by `marksObtained DESC`. Return ranked leaderboard.

### Step 3: Implement Frontend UI

1. **`src/app/(protected)/(staff-only)/students/[studentId]/page.tsx`**:
   - Add tab switcher:
     - **Profile & Academic Info:** Existing student profile details.
     - **Exam Results & Performance:** Data table with Exam Title, Subject, Date, Marks (Obtained / Max), Percentage, Status Badge.
     - **Chat & Activity:** Direct Stream Chat initiation link/embed.

2. **`src/app/(protected)/(teacher-only)/teacher/exams/[examId]/results/page.tsx`**:
   - Leaderboard scoreboard with student ranks, scores, submission timestamps, and CSV export.

### Step 4: Run tests to verify they pass
```bash
pytest backend/tests/students/test_student_exam_history.py
pnpm test run src/__tests__/components/student/StudentExamHistory.test.tsx
```

---

## Task 4: Principal-as-Teacher Hierarchy & Authorization Architecture

**Goal:** Enforce the hierarchy: Principal > Teacher > Student. Ensure Principals can perform all teacher actions (exam creation, question management, exam updates, class management) for their school.

**Files:**
- Modify: `backend/app/api/deps.py`
- Modify: `backend/app/exams/router.py`
- Modify: `src/app/(protected)/(principal-only)/principal/page.tsx`
- Test: `backend/tests/auth/test_principal_hierarchy.py`

### Step 1: Write failing backend hierarchy tests
`backend/tests/auth/test_principal_hierarchy.py`:
- Test that `get_current_staff_teacher` resolves teacher profile for `PRINCIPAL` and `TEACHER` roles.
- Test that a Principal can create, update, and release results for exams in their school.

### Step 2: Implement unified staff dependency

1. In `backend/app/api/deps.py`:
   ```python
   async def get_current_staff_teacher(
       current_user: Annotated[UserResponse, Depends(get_current_user)],
   ) -> Teacher:
       if current_user.role not in (Role.TEACHER, Role.PRINCIPAL, Role.ADMIN):
           raise HTTPException(
               status_code=403,
               detail="Only teachers or principals can perform this action.",
           )
       teacher = await get_teacher_by_user_id(current_user.id)
       if not teacher:
           raise HTTPException(
               status_code=403,
               detail="Staff profile not found. Please complete your profile setup.",
           )
       return teacher
   ```

2. In `backend/app/exams/router.py`:
   - Replace `get_teacher_from_user` with `get_current_staff_teacher`.
   - In `patch_exam` and `release_exam_results`, allow update if the user is the exam owner OR a principal belonging to the same school.

3. In `src/app/(protected)/(principal-only)/principal/page.tsx`:
   - Expose quick cards for "Create Exam", "My Exams", "Teacher Requests", and "Classes".

### Step 3: Run tests to verify they pass
```bash
pytest backend/tests/auth/test_principal_hierarchy.py
```

---

## Task 5: Teacher Class Join Requests & Principal Assignment System

**Goal:** Allow teachers to request to teach classes in their school, provide Principals with an approval/rejection inbox, and allow direct student and teacher assignment to classes.

**Files:**
- Modify: `backend/app/core/models.py` (add `TeacherClassJoinRequest`)
- Create: `backend/app/teacher_requests/` (`models.py`, `schemas.py`, `crud.py`, `router.py`)
- Modify: `backend/app/school_class/router.py`
- Modify: `backend/app/school_class/crud.py`
- Create: `src/app/(protected)/(principal-only)/principal/teacher-requests/page.tsx`
- Modify: `src/app/(protected)/(teacher-only)/teacher/classes/page.tsx`
- Modify: `src/components/navbars/AppSidebar.tsx`
- Test: `backend/tests/teacher_requests/test_teacher_class_requests.py`
- Test: `src/__tests__/components/principal/TeacherRequests.test.tsx`

### Step 1: Write failing tests

**Backend test (`backend/tests/teacher_requests/test_teacher_class_requests.py`):**
- Test `POST /api/v1/teacher-requests` creates a PENDING request.
- Test `GET /api/v1/teacher-requests/school/{school_id}` lists pending requests.
- Test `PATCH /api/v1/teacher-requests/{id}` with `APPROVED` creates `TeacherClass` record.
- Test `PATCH /api/v1/teacher-requests/{id}` with `REJECTED` sets status to REJECTED.
- Test `POST /api/v1/classes/{class_id}/assign-student` updates student's `classId`.
- Test `POST /api/v1/classes/{class_id}/assign-teacher` creates `TeacherClass` mapping.

### Step 2: Implement Backend

1. **`TeacherClassJoinRequest` Model in `backend/app/core/models.py`:**
   ```python
   class TeacherClassJoinRequest(Base):
       __tablename__ = "TeacherClassJoinRequest"
       __table_args__ = (
           UniqueConstraint("teacherId", "classId", name="teacherclassjoinrequest_teacherid_classid_key"),
           Index("teacherclassjoinrequest_teacherid_idx", "teacherId"),
           Index("teacherclassjoinrequest_classid_idx", "classId"),
       )
       id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
       teacherId: Mapped[str] = mapped_column(String, ForeignKey("Teacher.id", ondelete="CASCADE"), nullable=False)
       classId: Mapped[str] = mapped_column(String, ForeignKey("SchoolClass.id", ondelete="CASCADE"), nullable=False)
       subject: Mapped[Subject | None] = mapped_column(SQLEnum(Subject, native_enum=False), nullable=True)
       status: Mapped[JoinRequestStatus] = mapped_column(
           SQLEnum(JoinRequestStatus, native_enum=False), default=JoinRequestStatus.PENDING, nullable=False
       )
       requestedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
       decidedAt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
       decidedBy: Mapped[str | None] = mapped_column(String, nullable=True)

       teacher: Mapped["Teacher"] = relationship("Teacher")
       schoolClass: Mapped["SchoolClass"] = relationship("SchoolClass")
   ```

2. **Alembic DB Migration inside Docker:**
   ```bash
   alembic revision --autogenerate -m "add TeacherClassJoinRequest"
   alembic upgrade head
   ```

3. **`backend/app/teacher_requests/` Module:**
   - Implement `schemas.py`, `crud.py`, and `router.py` with endpoints:
     - `POST /api/v1/teacher-requests`
     - `GET /api/v1/teacher-requests/school/{school_id}`
     - `PATCH /api/v1/teacher-requests/{request_id}`

4. **Direct Assignment Endpoints in `backend/app/school_class/router.py`:**
   - `POST /api/v1/classes/{class_id}/assign-student`
   - `POST /api/v1/classes/{class_id}/assign-teacher`

### Step 3: Implement Frontend Pages

1. In `src/components/navbars/AppSidebar.tsx`: Add "Teacher Requests" nav item for `PRINCIPAL`.
2. In `src/app/(protected)/(principal-only)/principal/teacher-requests/page.tsx`:
   - Interactive inbox showing pending requests with Approve/Reject actions.
3. In `src/app/(protected)/(teacher-only)/teacher/classes/page.tsx`:
   - Add "Request to Teach Class" modal dialog.

### Step 4: Run tests to verify they pass
```bash
pytest backend/tests/teacher_requests/test_teacher_class_requests.py
pnpm test run src/__tests__/components/principal/TeacherRequests.test.tsx
```

---

## Task 6: Tab Favicon & Brand Icon Replacement

**Goal:** Change the browser tab icon to a modern vector SVG icon (Graduation Cap + Shield in indigo & violet gradients).

**Files:**
- Create: `src/app/icon.tsx` (Next.js dynamic 32×32 / 48×48 icon)
- Create: `src/app/apple-icon.tsx` (180×180 Apple touch icon)
- Create: `public/icon.svg` (Scalable vector icon)
- Modify: `src/app/layout.tsx` (Metadata icon configuration)
- Test: `src/__tests__/app/favicon.test.tsx`

### Step 1: Write test
```typescript
import { describe, it, expect } from "vitest";
import fs from "fs";

describe("Favicon Assets", () => {
  it("public/icon.svg exists and contains valid SVG structure", () => {
    const content = fs.readFileSync("public/icon.svg", "utf-8");
    expect(content).toContain("<svg");
    expect(content).toContain("</svg>");
  });
});
```

### Step 2: Implement icons & metadata
1. Create `public/icon.svg` with graduation cap and shield SVG paths.
2. Create `src/app/icon.tsx` and `src/app/apple-icon.tsx` using `ImageResponse`.
3. In `src/app/layout.tsx`, specify `icons: { icon: '/icon.svg', apple: '/apple-icon.png' }`.

### Step 3: Run test to verify it passes
```bash
pnpm test run src/__tests__/app/favicon.test.tsx
```

---

## Verification & Quality Checklist

1. **Docker Container Linting & Typing Checks:**
   - Frontend: `pnpm lint` and `pnpm type-check`
   - Backend: `ruff check .` and `ruff format .`
2. **Automated Test Suites:**
   - `pnpm test run` (Vitest)
   - `pytest backend/tests/` (Pytest)
3. **Database Migration:**
   - `alembic upgrade head`
4. **Manual E2E Verification:**
   - `/students` filter renders without school search inputs.
   - Exam builder surfaces explicit field-level error messages, allows past dates, and locks max marks to question mark totals.
   - Student detail page displays complete exam attempt scores, percentages, and direct chat links.
   - Principal can create exams, oversee school results, approve teacher class requests, and assign students/teachers to classes.
