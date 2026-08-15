# 🎓 ExamArena

ExamArena is a modern role-based examination and proctoring platform built for **Principals**, **Teachers**, and **Students**.

- **Frontend**: Next.js 16 (React 19), Tailwind CSS, Zustand, Vitest
- **Backend**: FastAPI, SQLAlchemy ORM, PostgreSQL

---

## 🔑 Test Credentials

Use the following seeded accounts to test different role permissions in the application:

| Role | Email | Password | Permissions & Scope |
|------|-------|----------|---------------------|
| **Admin** | `admin@gmail.com` | `karan166` | System Admin & School Creator |
| **Principal** | `principal@gmail.com` | `karan166` | Principal Dashboard, School & Class Management |
| **Teacher** | `teacher@gmail.com` | `karan166` | Exam Builder, Class Management, Auto/Manual Grading |
| **Student** | `student@gmail.com` | `karan166` | Student Assessments, Attempt Engine, Proctoring Enforcement |

---

## 🧪 Testing

Run unit tests locally:
```bash
pnpm test
```

---

## 🚀 Running Locally

```bash
# Install dependencies
pnpm install

# Run frontend development server
pnpm dev
```
