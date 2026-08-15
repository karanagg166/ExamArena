# ExamArena Platform Enhancements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement full India State/City selection, +91 10-digit phone validation, robust multi-role DOB persistence, human-readable class names, Stream Chat/WebSocket resilience with Redis testing, flexible exam scheduling with exam code & public access, section marks direct editing, advanced MSQ partial/negative grading, teacher-controlled evaluation/result release, and per-section timing controls.

**Architecture:**
- **Frontend (Next.js 16 App Router + Zustand + TailwindCSS):** New Indian State/City selector component, enhanced exam creation/edit forms with exam codes, section time limits, direct marks inputs, and negative marking toggles; exam start screen with code verification; exam results screen with pending vs published states; graceful StreamChat/WebSocket degradation.
- **Backend (FastAPI + SQLAlchemy 2.0 Async + Redis + NeonDB PostgreSQL):** Extended Pydantic schemas and database models for `Exam` (`isResultsReleased`, `isPublic`, `negativeMarking`, `negativeMarks`) and `ExamSection` (`durationMinutes`); updated user/student/teacher update schemas with `dateOfBirth` and `+91` phone regex validators; advanced grading engine supporting MSQ partial scoring and negative marks; evaluation release endpoint; comprehensive Redis test suite.

**Tech Stack:** Next.js 16, React 19, FastAPI, SQLAlchemy 2.0 Async, Redis (aioredis + REST + in-memory fallback), Pydantic v2, Zustand, Sonner, Vitest, Pytest.

---

### Task 1: India State and City Dataset & Selector Component

**Goal:** Provide an accurate, searchable dataset of all Indian States, Union Territories, and major cities with a reusable UI selector for signup and profile forms.

**Files:**
- Create: `src/lib/india-locations.ts`
- Create: `src/components/ui/IndiaStateCitySelect.tsx`
- Modify: `src/app/(public)/signup/page.tsx`
- Modify: `src/app/(public)/signup/principal/create-school/page.tsx`
- Modify: `src/app/(protected)/profile/page.tsx`
- Modify: `src/app/(protected)/(student-only)/student/profile/page.tsx`
- Modify: `src/app/(protected)/(teacher-only)/teacher/profile/page.tsx`
- Modify: `src/app/(protected)/(principal-only)/principal/profile/page.tsx`
- Test: `src/__tests__/lib/india-locations.test.ts`

**Step 1: Write unit test for India locations helper**
- Verify lookup of states and cities for states like Maharashtra, Delhi, Karnataka, Tamil Nadu, Uttar Pradesh, Gujarat, Punjab, etc.

**Step 2: Create `src/lib/india-locations.ts`**
- Export `INDIAN_STATES` (array of state names) and `INDIAN_CITIES_BY_STATE: Record<string, string[]>` with comprehensive coverage.
- Export helper functions `getStates()`, `getCitiesForState(state: string)`.

**Step 3: Create `src/components/ui/IndiaStateCitySelect.tsx`**
- Two responsive dropdowns/comboboxes: "State" and "City".
- When State changes, City dropdown automatically filters to the matching cities of that state.
- Supports manual search / write-in fallback if a user has a specific town.

**Step 4: Integrate selector across all signup and profile pages**
- Replace free-form State & City text inputs with `IndiaStateCitySelect`.

**Step 5: Run tests & verify**
- Run `pnpm test run` and `pnpm lint`.

---

### Task 2: Phone Number Validation (+91 with 10 Digits)

**Goal:** Enforce strict Indian phone number format (`+91` prefix followed by exactly 10 digits) on both frontend and backend.

**Files:**
- Modify: `src/lib/utils.ts`
- Modify: `backend/app/users/schemas.py`
- Modify: `backend/app/students/schemas.py`
- Modify: `backend/app/teachers/schemas.py`
- Modify: `backend/app/school/schemas.py`
- Test: `src/__tests__/lib/phone-validation.test.ts`
- Test: `backend/tests/users/test_phone_validation.py`

**Step 1: Update frontend `isValidPhoneNo` and `sanitizePhoneNo` in `src/lib/utils.ts`**
- Pattern: `/^\+91[6-9]\d{9}$/` or `/^\+91\d{10}$/`.
- Sanitizer: Preserves `+91` prefix and caps total digits to 10.
- Error message: `"Phone number must start with +91 followed by exactly 10 digits (e.g. +919876543210)"`.

**Step 2: Add Pydantic field validators in backend schemas**
- In `backend/app/users/schemas.py`, add validator on `phoneNo`:
  ```python
  @field_validator("phoneNo", mode="before")
  def validate_phone(cls, v: str) -> str:
      if not v:
          return v
      v = v.strip()
      if not re.match(r"^\+91\d{10}$", v):
          raise ValueError("Phone number must start with +91 followed by exactly 10 digits")
      return v
  ```
- Also validate optional parent, father, mother, and guardian phone numbers in `students/schemas.py`.

**Step 3: Run backend and frontend validation tests**
- Run `pytest backend/tests/users/` and `pnpm test run`.

---

### Task 3: Date of Birth (DOB) Persistence Across All User Roles

**Goal:** Fix the issue where DOB was not saving by including `dateOfBirth` in all nested update schemas and fixing payload structures on profile forms.

**Files:**
- Modify: `backend/app/students/schemas.py` (Add `dateOfBirth: datetime | None = None` to `UserUpdateNested`)
- Modify: `backend/app/teachers/schemas.py` (Add `dateOfBirth: datetime | None = None` to `UserUpdateNested`)
- Modify: `src/app/(protected)/(student-only)/student/profile/page.tsx`
- Modify: `src/app/(protected)/(teacher-only)/teacher/profile/page.tsx`
- Modify: `src/app/(protected)/(principal-only)/principal/profile/page.tsx`
- Modify: `src/app/(protected)/profile/page.tsx`
- Test: `backend/tests/student/test_student_dob_update.py`
- Test: `backend/tests/teacher/test_teacher_dob_update.py`

**Step 1: Write backend tests for DOB updates via student/teacher profile endpoints**
- Test sending `{"user": {"dateOfBirth": "2005-04-12T00:00:00Z"}}` to `/api/v1/students/me` and `/api/v1/teachers/me`. Verify `user.dateOfBirth` is persisted and returned.

**Step 2: Update backend schemas & CRUD**
- Add `dateOfBirth: datetime | None = None` to `UserUpdateNested` in `students/schemas.py` and `teachers/schemas.py`.
- Ensure date serialization/deserialization handles ISO strings and date objects cleanly.

**Step 3: Update frontend profile forms**
- In `student/profile/page.tsx`, read initial `data?.user?.dateOfBirth` (formatted `YYYY-MM-DD`).
- When saving student profile, send `user: { ...formData, dateOfBirth: formData.dob }`.
- Ensure teacher, principal, and general account settings pages all read and save `dateOfBirth` reliably.

**Step 4: Run tests**
- Run `pytest` and `pnpm type-check`.

---

### Task 4: Human-Readable Class Name Display Across Teacher & Student Views

**Goal:** Ensure that wherever a class is viewed, the human-readable class name (e.g. "Grade 11A") is displayed instead of the internal UUID/CUID `classId`.

**Files:**
- Modify: `src/app/(protected)/(teacher-only)/teacher/classes/[classId]/page.tsx`
- Modify: `src/app/(protected)/(principal-only)/principal/school/classes/[classId]/page.tsx`
- Modify: `src/components/school-class/ClassStudentsList.tsx`
- Modify: `src/app/(protected)/(student-only)/student/class/page.tsx`
- Modify: `src/app/(protected)/(teacher-only)/teacher/classes/[classId]/requests/page.tsx`

**Step 1: Audit and replace raw `classId` display strings**
- In `teacher/classes/[classId]/page.tsx`: replace `<span className="text-zinc-500">Class ID:</span> {schoolClass.id}` with `<span className="text-zinc-500">Class Name:</span> {schoolClass.name}`.
- In `principal/school/classes/[classId]/page.tsx`: show `schoolClass.name`.
- In `ClassStudentsList.tsx`: fetch or accept `className` prop and replace generic `"registered to this class ID"` text with `"registered to this class"`.
- In `requests/page.tsx`: show the class name in header and breadcrumb (`schoolClass.name` instead of raw ID).

**Step 2: Verify and run frontend tests**
- Run `pnpm type-check` and `pnpm lint`.

---

### Task 5: Stream Chat / WebSocket Resilience & Redis Integration with Tests

**Goal:** Fix unhandled WebSocket connection errors from Stream Chat, implement graceful offline/fallback handling, and add comprehensive test cases for Redis caching and pub/sub capabilities.

**Files:**
- Modify: `src/app/(protected)/(any-auth)/chat/page.tsx`
- Modify: `backend/app/core/redis.py`
- Modify: `backend/app/auth/router.py`
- Create: `backend/tests/core/test_redis.py`

**Step 1: Fix StreamChat WebSocket connection error handling in `chat/page.tsx`**
- Wrap Stream connection logic with error boundaries and connection timeout handlers.
- If Stream API keys are not configured or WebSocket connection fails, display a clean fallback UI with status: "Chat service is temporarily offline or initializing. Please retry in a moment." without throwing unhandled console rejections.
- Gracefully disconnect on component unmount.

**Step 2: Enhance Redis client and helpers in `backend/app/core/redis.py`**
- Ensure support for Redis operations (`get`, `set`, `setex`, `delete`, `exists`, `ping`) across `aioredis`, `UpstashRedisRESTClient`, and `InMemoryRedisFallback`.

**Step 3: Write comprehensive Redis test cases in `backend/tests/core/test_redis.py`**
- Test Redis set/get with TTL.
- Test JWT token blacklist caching and validation.
- Test student attempt caching in Redis.
- Test fallback behavior when Redis connection is unavailable.

**Step 4: Run pytest on Redis test suite**
- Run `pytest backend/tests/core/test_redis.py -v`.

---

### Task 6: Exam Scheduling, Exam Code Access, and Public Exam Option

**Goal:** Support scheduling where exams can be taken at any time *after* the scheduled start time, with two access modes: Public to school or Code-protected (requiring students to enter the exam code).

**Files:**
- Modify: `backend/app/core/models.py` (Add `isPublic: Mapped[bool]` to `Exam` if needed)
- Modify: `backend/prisma/schema.prisma`
- Modify: `backend/app/exams/schemas.py`
- Modify: `backend/app/exams/crud.py`
- Modify: `backend/app/attempts/router.py` & `crud.py`
- Modify: `src/types/exam.ts`
- Modify: `src/components/exam/ExamForm.tsx`
- Modify: `src/app/(protected)/(student-only)/student/exams/[examId]/start/page.tsx`
- Modify: `src/app/(protected)/(teacher-only)/teacher/exams/[examId]/page.tsx`
- Test: `backend/tests/exams/test_exam_code_and_access.py`

**Step 1: Backend schema & model updates**
- In `ExamBase`: add `isPublic: bool = True`, `examCode: str | None = None`.
- In `start_exam_attempt`: check if current time is after `scheduledAt`. If not yet started, return error "Exam has not started yet. Scheduled start time: ...".
- If `isPublic == False`, require `examCode` in `StudentExamCreate` and verify it matches `exam.examCode`.

**Step 2: Frontend exam creation & start screen**
- In `ExamForm.tsx`: add Exam Code input (with "Generate Code" button) and Access Mode toggle ("Public to school students" vs "Passcode protected").
- In `student/exams/[examId]/start/page.tsx`: if exam requires a code, render an Exam Code input field before unlocking the "Begin Exam" button.

**Step 3: Run backend and frontend tests**
- Run `pytest backend/tests/exams/` and `pnpm test run`.

---

### Task 7: Direct Question Marks Editing & Validation Warnings

**Goal:** Enable teachers to directly enter question marks (e.g. 4, 5) without annoying auto-overwriting, and display clear warnings if invalid/non-positive marks are entered.

**Files:**
- Modify: `src/components/question/QuestionList.tsx`
- Modify: `src/components/question/QuestionCard.tsx`
- Modify: `src/app/(protected)/(teacher-only)/teacher/exams/create/page.tsx`
- Modify: `src/app/(protected)/(teacher-only)/teacher/exams/[examId]/edit/page.tsx`
- Test: `src/__tests__/components/sections.test.ts`

**Step 1: Fix marks input behavior in `QuestionList.tsx`**
- Allow direct editing of marks per question and per section without aggressive `Math.max(1, ...)` reset on each keystroke.
- Validate on blur / submit: if `<= 0`, show warning message in form and prevent submission.

**Step 2: Add validation alerts**
- If teacher enters 0 or negative marks, highlight the field with a red border and warning text: "Marks per question must be greater than 0".

**Step 3: Run frontend tests**
- Run `pnpm test run`.

---

### Task 8: Multiple Select (MSQ) & MCQ Auto-Grading (Negative & Partial Marking)

**Goal:** Implement exact grading formulas for Multiple Select (MSQ), Single Choice MCQ, and True/False questions with configurable negative marking and proportional partial credit.

**Files:**
- Modify: `backend/app/core/models.py` (Add `negativeMarking: Mapped[bool]`, `negativeMarks: Mapped[float]` to `Exam`)
- Modify: `backend/prisma/schema.prisma`
- Modify: `backend/app/exams/schemas.py`
- Modify: `backend/app/attempts/crud.py` (Implement grading engine)
- Modify: `src/types/exam.ts`
- Modify: `src/components/exam/ExamForm.tsx` (Add Negative Marking toggle & penalty inputs)
- Test: `backend/tests/attempts/test_msq_grading.py`

**Grading Engine Rules:**
- **Multiple Select (MSQ):**
  - Total correct options = $C$, Student correct picks = $K_{correct}$, Student incorrect picks = $K_{wrong}$.
  - If $K_{wrong} > 0$:
    - If `exam.negativeMarking` is enabled & penalty set &rarr; deduct penalty (e.g. $-1$ mark).
    - If no negative marking &rarr; 0 marks.
  - If $K_{wrong} == 0$ and $K_{correct} == C$: Full marks.
  - If $K_{wrong} == 0$ and $0 < K_{correct} < C$: Partial marks = $(K_{correct} / C) \times \text{question.marks}$.
  - If no options selected: 0 marks.
- **Single Choice MCQ & True/False:**
  - Correct: Full marks.
  - Incorrect: $- \text{negativeMarks}$ if negative marking enabled, else 0 marks.
  - Unattempted: 0 marks.

**Step 1: Write unit tests for grading logic in `backend/tests/attempts/test_msq_grading.py`**
- Test all cases: full correct, partial without wrong options, partial with 1 wrong option + negative marking on/off, unattempted.

**Step 2: Implement grading algorithm in `backend/app/attempts/crud.py`**
- Implement `calculate_question_score(question, student_answer, negative_marking, negative_marks)` helper.

**Step 3: Run pytest**
- Run `pytest backend/tests/attempts/test_msq_grading.py -v`.

---

### Task 9: Teacher Exam Evaluation & Result Release Workflow

**Goal:** Allow teachers to manually evaluate and release exam results. When released, all students see scores and answer keys; submissions made after release receive immediate instant results.

**Files:**
- Modify: `backend/app/core/models.py` (Add `isResultsReleased: Mapped[bool]` to `Exam`)
- Modify: `backend/prisma/schema.prisma`
- Modify: `backend/app/exams/router.py` (Add `POST /api/v1/exams/{id}/release-results`)
- Modify: `backend/app/exams/crud.py`
- Modify: `backend/app/attempts/crud.py` & `router.py`
- Modify: `src/app/(protected)/(teacher-only)/teacher/exams/[examId]/page.tsx`
- Modify: `src/app/(protected)/(student-only)/student/exams/[examId]/result/page.tsx`
- Test: `backend/tests/exams/test_result_release.py`

**Step 1: Create backend endpoint `POST /api/v1/exams/{id}/release-results`**
- Only authorized teacher (owner of the exam) can trigger.
- Evaluates and grades all submitted attempts.
- Sets `exam.isResultsReleased = True`.
- In `submit_exam_attempt`: if `exam.isResultsReleased == True`, immediately auto-grade the attempt.

**Step 2: Update student attempt result page (`student/exams/[examId]/result/page.tsx`)**
- If `exam.isResultsReleased == False`:
  - Show "Exam Submitted" confirmation with notice: "Your submission has been safely recorded. Results and answer keys will be published once the teacher releases evaluations."
- If `exam.isResultsReleased == True`:
  - Display score summary card (Marks Obtained / Max Marks, Percentage, Accuracy, Time Taken).
  - Display detailed Question Breakdown & Answer Key (Correct answer, Student's chosen answer, explanation, marks awarded).

**Step 3: Add "Release Results & Answer Keys" action on teacher exam view page**
- Badge showing "Results: Pending Release" or "Results: Published".
- Button to trigger release with confirmation dialog.

**Step 4: Run backend & frontend tests**
- Run `pytest backend/tests/exams/` and `pnpm test run`.

---

### Task 10: Section Timing Controls & Flexible Time Allocation

**Goal:** Allow teachers to set individual time limits per section, validate against total exam duration, allow remaining sections to share remaining time, and enforce section timers in the student exam interface.

**Files:**
- Modify: `backend/app/core/models.py` (Add `durationMinutes: Mapped[int | None]` to `ExamSection`)
- Modify: `backend/prisma/schema.prisma`
- Modify: `backend/app/sections/schemas.py` & `crud.py`
- Modify: `src/types/section.ts`
- Modify: `src/components/question/QuestionList.tsx`
- Modify: `src/components/exam/ExamForm.tsx`
- Modify: `src/hooks/useExamTimer.ts`
- Modify: `src/app/(protected)/(student-only)/student/exams/[examId]/attempt/page.tsx`
- Test: `src/__tests__/hooks/useExamTimer.test.ts`
- Test: `backend/tests/sections/test_section_duration.py`

**Step 1: Section duration schema & validation**
- In `SectionBase`: `durationMinutes: int | None = None`.
- In `QuestionList.tsx` and `ExamForm.tsx`:
  - Teacher can optionally assign duration (in minutes) to any section.
  - Form validates that the sum of section durations does NOT exceed total exam duration. If sum != total duration and some sections have no limit, show helpful info banner: "Sections without a specific time limit will share the remaining X minutes."
  - If sum of specified section durations exceeds total duration, show error warning: "Total section time (X mins) exceeds exam duration (Y mins)".

**Step 2: Section timer enforcement during attempt**
- In `useExamTimer.ts` and `attempt/page.tsx`:
  - Track current active section.
  - If the active section has a `durationMinutes` set, show both the Section Timer and Global Exam Timer.
  - When the section time expires, automatically transition student to the next section.
  - Global exam timer continues to tick down total remaining exam time.

**Step 3: Run frontend timer tests and backend section tests**
- Run `pnpm test run` and `pytest backend/tests/sections/`.

---

### Task 11: End-to-End Validation, Docker Checks & Documentation

**Goal:** Run full end-to-end linting, type-checking, backend tests, frontend tests, and database migrations inside Docker containers.

**Step 1: Run backend checks in Docker container**
- `docker compose exec -T backend ruff check .`
- `docker compose exec -T backend ruff format --check .`
- `docker compose exec -T backend pytest`

**Step 2: Run frontend checks in Docker container**
- `docker compose exec -T frontend pnpm lint`
- `docker compose exec -T frontend pnpm type-check`
- `docker compose exec -T frontend pnpm test run`
