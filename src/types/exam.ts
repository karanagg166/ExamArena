import type { Question, QuestionCreate, QuestionUpsert } from "./question";

// ─── Enums (match Prisma) ───────────────────────────────────────────────────
export type ExamType = "MIDTERM" | "FINAL" | "QUIZ" | "ASSIGNMENT" | "MOCK";

export type Subject =
  | "MATHS"
  | "SCIENCE"
  | "HISTORY"
  | "LITERATURE"
  | "ART"
  | "MUSIC"
  | "PHYSICAL_EDUCATION";

// ─── Exam ───────────────────────────────────────────────────────────────────
// Matches Prisma: Exam model
export type Exam = {
  id: string;
  name: string;
  description: string;
  scheduledAt: string; // Prisma field is "scheduledAt", not "date"
  duration: number;
  maxMarks: number;
  instructions?: string;
  isPublished: boolean;
  subject?: Subject;
  type: ExamType;
  teacherId: string;
  createdAt: string;
  updatedAt: string;
  questions?: Question[];
  teacher?: {
    id: string;
    user: {
      name: string;
    };
    school?: {
      name: string;
    };
  };
};

// Teacher creating an exam — no id/timestamps/teacherId
export type ExamCreate = Omit<Exam, "id" | "createdAt" | "updatedAt" | "questions" | "teacherId"> & {
  questions?: QuestionCreate[];
};

// Teacher updating an exam — id required, rest optional
// Questions use QuestionUpsert: has id → update, no id → create new
export type ExamUpdate = Partial<
  Omit<Exam, "updatedAt" | "questions">
> & {
  id: string; // required — which exam to update
  questions?: QuestionUpsert[]; // mix of existing (with id) and new (without id)
};
