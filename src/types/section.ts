import type { Question, QuestionType } from "./question";

// ─── Section ────────────────────────────────────────────────────────────────
// Matches backend ExamSection model
export type Section = {
  id: string;
  name: string; // "Section A", "Section B", etc.
  description?: string;
  questionType: QuestionType;
  marksPerQuestion: number;
  durationMinutes?: number;
  sortOrder: number;
  examId: string;
  createdAt: string;
  updatedAt: string;
  questions?: Question[];
};

// Teacher creating a section — no id/timestamps (server-generated)
export type SectionCreate = {
  name: string;
  description?: string;
  questionType: QuestionType;
  marksPerQuestion: number;
  durationMinutes?: number;
  examId: string;
};

// Teacher updating a section — all fields optional
export type SectionUpdate = {
  description?: string;
  questionType?: QuestionType;
  marksPerQuestion?: number;
  durationMinutes?: number;
};
