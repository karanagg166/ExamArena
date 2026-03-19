# Setup Guide

Follow this guide to run Exam Arena locally.

## Prerequisites

- Node.js 20+
- npm 10+
- Python 3.10+ (for FastAPI backend)
- Docker & Docker Compose (Strongly Recommended)
- PostgreSQL 15+ (if running natively without Docker)

## 🆕 New Libraries & Tools to Install (And Why We Need Them)

Based on the project's end goals (AI evaluation, secure browser proctoring, PDF parsing, and document exporting), you will need to add the following libraries to your tech stack. Here is the exact reason why each tool was selected:

### Frontend (Next.js)

```bash
# Exporting results (Sheets/PDFs)
npm install xlsx jspdf jspdf-autotable

# Camera/Mic access for proctoring
npm install react-webcam
```
**Rationale:**
- `xlsx`: Allows teachers to download detailed class scores directly into an Excel spreadsheet for off-platform grading or school records.
- `jspdf` & `jspdf-autotable`: Enables generating formatted PDF report cards for students and teachers directly from the browser.
- `react-webcam`: Provides a simple React interface to turn on the student's camera and microphone during an exam. We capture this feed to enforce the "Secure Environment" requirement.
*(Note: Basic tab-switching detection will be handled using the native browser `visibilitychange` API. True system lockdown requires custom desktop apps).*

### Backend (Python / FastAPI)

```bash
# AI Integration & Document Parsing
pip install openai langchain python-dotenv
pip install PyPDF2 pdfplumber  # For reading uploaded PDFs

# Proctoring (Optional if analyzing feeds on backend)
pip install opencv-python face_recognition

# Data processing & Exporting
pip install pandas openpyxl reportlab

# Storage & Background Tasks
pip install boto3 arq
```
**Rationale:**
- `openai` & `langchain`: The core tools used to integrate ChatGPT/LLMs. They will analyze the "short answer" texts submitted by students and evaluate them against the teacher's rubric. They will also process syllabus guidelines to auto-generate question papers.
- `PyPDF2` & `pdfplumber`: When a teacher uploads a PDF of a previous exam and an answer key, these libraries extract the raw text and images so the AI can understand and digitize it into the system.
- `opencv-python` & `face_recognition`: If we want to do "smart proctoring" (e.g., detecting if a user looks away from the screen for 10 seconds, or if two faces appear in the webcam), OpenCV processes the video feed, and `face_recognition` flags rule violations.
- `pandas`, `openpyxl`, `reportlab`: Powerful backend tools. If Excel/PDF reports are too massive for the frontend to generate, the backend can crunch thousands of student records at once using Pandas and return a clean download link.
- `boto3`: The standard AWS SDK for Python. Because Cloudflare R2 is perfectly S3-compatible, we use `boto3` to instantly store and retrieve all PDF question papers from R2 seamlessly.
- `arq`: An Async Redis job runner designed precisely for speed in FastAPI architectures. It prevents the server from freezing during complex AI background tasks (far easier to scale than Celery).

## 🛠 Required & Recommended VS Code Extensions

To ensure a smooth development experience across this stack, please install the following extensions in VS Code:
1. **Python** (by Microsoft)
2. **Pylance** (by Microsoft)
3. **Docker** (by Microsoft)
4. **Prisma** (by Prisma)
5. **Tailwind CSS IntelliSense** (by Tailwind Labs)
6. **ESLint** (by Microsoft)
7. **Prettier - Code formatter** (by Prettier)
8. **Ruff** (by Astral Software) - *For extremely fast Python linting and formatting*

---

## 1. Install Dependencies

**Frontend:**
```bash
npm install
```

**Backend:**
```bash
# (Assuming backend is placed in a /backend folder)
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configure Environment Variables

Create your local env file from the template:
```bash
cp .env.example .env
```
Update `DATABASE_URL` in `.env` with your database connection string, and add your `OPENAI_API_KEY` or equivalent for the AI features.

## 3. Generate Prisma Client
```bash
npx prisma generate
```

## 4. Starting the Application (Using Docker)

Since we have a frontend, a Python backend, a database, and potentially Redis for background tasks, **using Docker is highly recommended**. 
Please refer to the `docker-compose.yml` file in the root directory.

To start everything simultaneously:
```bash
docker-compose up --build
```

If you wish to run them natively without Docker:
- Start Postgres locally.
- Run frontend: `npm run dev`
- Run backend: `cd backend && uvicorn main:app --reload`
