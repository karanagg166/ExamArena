# Exam Arena — Feature List

> Medium-sized features for two-person development. Each feature is 1–4 days of work.
> Branch format: `feature/<feature-name>` → PR into `deploy`.

---

## ✅ Already Done

| # | Feature |
|---|---------|
| 1 | User signup / login (JWT cookie auth) |
| 2 | `/api/v1/auth/me`, `/logout` endpoints |
| 3 | Auth unit + integration tests (pytest) |

---

## 🟡 Foundation — Do These First (others depend on them)

| # | Feature | Branch Name | Notes |
|---|---------|-------------|-------|
| F1 | **Prisma schema: Exam, Question, ExamAttempt models** | `feature/exam-schema` | Add `Exam`, `Question`, `Option`, `ExamAttempt`, `Answer` to `schema.prisma` + `prisma db push` |
| F2 | **Role-based middleware** | `feature/role-middleware` | Backend guards like `require_role("TEACHER")` in `deps.py`. Needed before any role-specific endpoints |
| F3 | **Student profile setup** | `feature/student-profile` | API: create/get student profile (rollNo, class, dob). Frontend: profile completion page after signup |
| F4 | **Teacher profile setup** | `feature/teacher-profile` | API: create/get teacher profile (qualification, department). Frontend: profile completion page after signup |

---

## 🟠 Exam Management

| # | Feature | Branch Name | Notes |
|---|---------|-------------|-------|
| E1 | **Create exam (Teacher)** | `feature/create-exam` | Backend: `POST /api/v1/exams` — title, duration, type (MCQ/short), start time. Frontend: exam creation form |
| E2 | **Add questions to exam** | `feature/add-questions` | Backend: `POST /api/v1/exams/{id}/questions` — MCQ with 4 options + correct answer, marks, negative marking. Frontend: question builder |
| E3 | **Student exam list** | `feature/student-exam-list` | Backend: `GET /api/v1/exams` filtered by student's class. Frontend: list with status (upcoming / live / done) |
| E4 | **Exam attempt flow** | `feature/exam-attempt` | Backend: `POST /api/v1/exams/{id}/start`, save answers. Frontend: question-by-question UI with Zustand timer |
| E5 | **Submit exam & auto-score MCQ** | `feature/exam-submit` | Backend: `POST /api/v1/exams/{id}/submit` — calc score, handle negative marking, save result |
| E6 | **View exam result (Student)** | `feature/student-results` | Backend: `GET /api/v1/exams/{id}/result`. Frontend: score breakdown page |

---

## 🔵 Teacher Dashboard

| # | Feature | Branch Name | Notes |
|---|---------|-------------|-------|
| T1 | **Teacher exam dashboard** | `feature/teacher-dashboard` | Frontend: list of teacher's exams with live/draft/ended status and quick stats |
| T2 | **View class results (Teacher)** | `feature/class-results` | Backend: `GET /api/v1/exams/{id}/results` (all students). Frontend: results table |
| T3 | **Export results to Excel / PDF** | `feature/export-results` | Backend: generate `.xlsx` (openpyxl) + `.pdf` (reportlab). Frontend: export buttons |

---

## 🟣 AI Features

| # | Feature | Branch Name | Notes |
|---|---------|-------------|-------|
| A1 | **PDF question paper parser** | `feature/pdf-parser` | Backend: accept PDF upload, use pdfplumber + OpenAI to extract questions + options → return JSON |
| A2 | **AI question paper import UI** | `feature/ai-import-questions` | Frontend: upload PDF → preview extracted questions → confirm + save to exam. Depends on A1 |
| A3 | **AI short-answer evaluator** | `feature/ai-short-answer` | Backend: after submit, send short-answer responses to OpenAI with rubric → return score + feedback |

---

## 🔴 Proctoring

| # | Feature | Branch Name | Notes |
|---|---------|-------------|-------|
| P1 | **Tab/window switch detection** | `feature/tab-switch-detect` | Frontend only: `visibilitychange` + `blur` events, count violations, warn/auto-submit after threshold |
| P2 | **Fullscreen enforcement** | `feature/fullscreen-lock` | Frontend only: force fullscreen on start, detect exit, show warning + auto-submit |
| P3 | **Webcam snapshot proctoring** | `feature/webcam-proctor` | Frontend: `react-webcam` snapshots every 30s. Backend: store via ARQ background job |

---

## 🟤 Admin / Multi-Tenant

| # | Feature | Branch Name | Notes |
|---|---------|-------------|-------|
| M1 | **Class management** | `feature/class-management` | Backend: CRUD for `Class` — create class, assign teacher, enroll students. Frontend: admin class page |
| M2 | **Student analytics dashboard** | `feature/student-analytics` | Frontend: student score history, avg score, weak subject chart |

---

## 🔗 Real-Time

| # | Feature | Branch Name | Notes |
|---|---------|-------------|-------|
| R1 | **Exam live broadcast** | `feature/exam-broadcast` | Backend: teacher pushes "exam started" via Socket.IO. Frontend: student lobby auto-navigates |

---

## 💡 Suggested First Split

| You | Friend |
|-----|--------|
| **F1** — Exam schema | **F2** — Role middleware |
| **E1** — Create exam | **F3 or F4** — Student/Teacher profile |
| **E4** — Exam attempt flow | **T1** — Teacher dashboard |
