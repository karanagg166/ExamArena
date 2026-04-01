import type { QuestionType } from "./question";

// ─── Enums (match Prisma) ───────────────────────────────────────────────────
export type AttemptStatus =
  | "IN_PROGRESS"
  | "SUBMITTED"
  | "GRADED"
  | "EXPIRED"
  | "NOT_ATTEMPTED";

export type GradingStatus = "PENDING" | "AUTO_GRADED" | "MANUALLY_GRADED";

export type Correctness = "FULLY_CORRECT" | "PARTIALLY_CORRECT" | "INCORRECT";

// ─── SelectedOption (Prisma: SelectedOption) ────────────────────────────────
// Tracks which option(s) a student selected for a question

export type SelectedOption = {
  id: string;
  studentExamAnswerId: string;
  optionId: string;
};

// Frontend sends only optionId — server links it to the answer
export type SelectedOptionCreate = {
  optionId: string;
};

// ─── StudentExamAnswer (Prisma: StudentExamAnswer) ──────────────────────────
// One answer per question in an attempt

export type StudentAnswer = {
  id: string;
  studentExamId: string;
  questionId: string;
  questionType: QuestionType;
  textAnswer?: string;
  marksAwarded?: number;
  feedback?: string;
  isCorrect?: Correctness;
  gradingStatus: GradingStatus;
  createdAt: string;
  updatedAt: string;
  selectedOptions?: SelectedOption[];
};

// When starting exam: create empty answer shells (no textAnswer/selectedOptions yet)
export type StudentAnswerCreate = {
  questionId: string;
  questionType: QuestionType;
};

// When submitting: student fills in their answer for a question
export type StudentAnswerUpdate = {
  id: string; // which answer record to update
  textAnswer?: string;
  selectedOptions?: SelectedOptionCreate[]; // options chosen by student
};

// ─── StudentExam (Prisma: StudentExam) ──────────────────────────────────────
// The top-level attempt record linking student ↔ exam

export type StudentExam = {
  id: string;
  studentId: string;
  examId: string;
  marksObtained: number;
  startedAt: string;
  submittedAt?: string;
  status: AttemptStatus;
  answers?: StudentAnswer[];
};

// When starting exam: frontend sends just examId
// Server injects studentId (from JWT), startedAt (now), status (IN_PROGRESS)
export type StudentExamCreate = {
  examId: string;
};

// When submitting exam: send all answers at once
export type StudentExamSubmit = {
  id: string; // which attempt to submit
  answers: StudentAnswerUpdate[]; // all filled-in answers
};

// For teacher/admin grading or status updates
export type StudentExamUpdate = {
  id: string;
  marksObtained?: number;
  status?: AttemptStatus;
  submittedAt?: string;
};
