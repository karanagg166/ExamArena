# Project Goals & Features

Exam Arena is a comprehensive, secure, and AI-powered examination platform designed to serve multiple schools, handle various educational roles, and provide a highly secure environment for conducting online tests.

## 🎯 End Goal & Vision

The primary goal of Exam Arena is to provide a robust, scalable system that allows schools to administer exams (like JEE Mains, NEET, and standard school tests) securely. The platform aims to eliminate cheating through strict proctoring features while greatly reducing teacher workload through AI-driven automated question paper generation and short-answer evaluation.

## 👥 User Roles

1. **System Admin**
   - The overarching administrator of the entire platform.
   - Manages different schools, base configurations, and global settings.
2. **Superadmin (Principals / Management)**
   - Manages an individual school's operations.
   - Oversees teachers, students, and overall statistics for their specific school.
3. **Admin (Teachers)**
   - Creates and manages classes, test papers, and grading.
   - Views and exports student results.
4. **Students**
   - Takes tests tailored for them.
   - Views their own scores and performance analytics securely.

## 🚀 Core Features & To-Do List

### 1. Test Creation & Management
- [ ] Support for multiple exam types (JEE Mains, NEET, custom).
- [ ] **Privacy Controls:** Test papers can be marked *Public* or *Private* (accessible via a unique secure key).
- [ ] Question bank with categories and difficulty levels.
- [ ] AI Question Paper Generation: Teachers can upload a PDF with a question paper and an answer key. The system will automatically parse the document and generate the digital question paper and answer key within the platform.

### 2. Secure Exam Environment (Proctoring)
- [ ] **Lockdown Mode:** Prevent screen switching or tab switching during the exam.
- [ ] **Live Monitoring:** Camera and microphone tracking to detect suspicious activities.
- [ ] Full-screen enforcement and disabling of copy-paste/keyboard shortcuts.

### 3. Automated Grading & AI Evaluation
- [ ] Automatic calculation of scores for Multiple Choice and standard questions.
- [ ] **AI Short-Answer Evaluation:** Integration of AI models to contextually evaluate and score subjective/short-answer questions.
- [ ] Result calculation, score breakdown, and negative marking handling (e.g., for JEE/NEET formats).

### 4. Reporting & Analytics
- [ ] Analytics dashboard for students to view their performance.
- [ ] Dashboard for teachers to monitor aggregate class performance.
- [ ] **Result Exporting:** Teachers can export exam results and analytics into various formats (Excel/Sheets, PDF, DOCX).

### 5. Multi-Tenant Architecture
- [ ] School segregation handling so multiple schools can use the platform securely and independently.
- [ ] Class and batch management within each school.
