import type { Question, QuestionCreate, QuestionUpsert } from "./question";
import type { Section, SectionCreate } from "./section";

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
  examCode?: string;
  name: string;
  description: string;
  scheduledAt: string; // Prisma field is "scheduledAt", not "date"
  duration: number;
  maxMarks: number;
  instructions?: string;
  isPublished: boolean;
  isPublic: boolean;
  isResultsReleased: boolean;
  negativeMarking: boolean;
  negativeMarks: number;
  subject?: Subject;
  type: ExamType;
  teacherId: string;
  createdAt: string;
  updatedAt: string;
  questions?: Question[];
  sections?: Section[];
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
export type ExamCreate = Omit<
  Exam,
  | "id"
  | "createdAt"
  | "updatedAt"
  | "questions"
  | "teacherId"
  | "isPublic"
  | "isResultsReleased"
  | "negativeMarking"
  | "negativeMarks"
> & {
  isPublic?: boolean;
  isResultsReleased?: boolean;
  negativeMarking?: boolean;
  negativeMarks?: number;
  questions?: QuestionCreate[];
  sections?: SectionCreate[];
};

// Teacher updating an exam — id required, rest optional
// Questions use QuestionUpsert: has id → update, no id → create new
export type ExamUpdate = Partial<
  Omit<Exam, "updatedAt" | "questions">
> & {
  id: string; // required — which exam to update
  questions?: QuestionUpsert[]; // mix of existing (with id) and new (without id)
};
