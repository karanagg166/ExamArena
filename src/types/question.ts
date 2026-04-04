// ─── Enums (match Prisma QuestionType) ──────────────────────────────────────
export type QuestionType =
  | "MULTIPLE_CHOICE"
  | "MULTIPLE_SELECT"
  | "TRUE_FALSE"
  | "SHORT_ANSWER"
  | "ESSAY";

// ─── QuestionOption ─────────────────────────────────────────────────────────
// Matches Prisma: QuestionOption (no createdAt/updatedAt in schema)
export type QuestionOption = {
  id: string;
  optionNumber: number;
  questionId: string;
  text: string;
  isCorrect: boolean;
  imageUrl?: string;
};

// For teacher creating options — no id/questionId (server-generated)
export type QuestionOptionCreate = Omit<QuestionOption, "id" | "questionId">;

// ─── Question ───────────────────────────────────────────────────────────────
// Matches Prisma: Question model
export type Question = {
  id: string;
  questionNumber: number;
  text: string;
  section: string;
  marks: number;
  imageUrl?: string;
  wordLimit?: number;
  explanation?: string;
  questionType: QuestionType; // Prisma field name is "questionType", not "type"
  examId: string;
  createdAt: string;
  updatedAt: string;
  options?: QuestionOption[];
};

// Teacher creating a question — no id/timestamps (server-generated)
export type QuestionCreate = Omit<
  Question,
  "id" | "createdAt" | "updatedAt" | "options"
> & {
  options?: QuestionOptionCreate[];
};

// Upsert: has id → update existing question, no id → create new question
// Used inside ExamUpdate when some questions already exist and some are new
export type QuestionUpsert = QuestionCreate & { id?: string };
