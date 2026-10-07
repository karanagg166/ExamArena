// Teacher-only contracts from backend/app/grading/schemas.py.
// Keep these out of student stores and student answer components.
import type { QuestionType } from "./question";
import type {
  Correctness,
  GradingStatus,
  StudentExam,
  StudentAnswer,
} from "./attempt";

export interface RubricGrade {
  criterion: string;
  maxMarks: number;
  awardedMarks: number;
  justification: string;
}
export interface AIGradingProposal {
  answerId: string;
  suggestedMarks: number;
  maxMarks: number;
  rubricBreakdown: RubricGrade[];
  feedback: string;
  confidence: string; // Response schema is a string; service emits HIGH/MEDIUM/LOW.
  warnings: string[];
}
export interface TeacherGrade {
  answerId: string;
  studentExamId: string;
  questionId: string;
  marksAwarded: number;
  maxMarks: number;
  feedback: string | null;
  gradingStatus: GradingStatus;
  gradedBy: string | null;
  gradedAt: string | null;
  isCorrect: Correctness | null;
}
export interface TeacherAnswerDetail {
  id: string;
  studentExamId: string;
  questionId: string;
  questionType: QuestionType;
  questionNumber: number;
  questionText: string;
  maxMarks: number;
  studentAnswer: string | null;
  referenceAnswer: string | null;
  // Backend allows arbitrary rubric dictionaries; narrow values when rendering.
  gradingRubric: Record<string, unknown>[] | null;
  explanation: string | null;
  aiProposal: AIGradingProposal | null;
  finalGrade: TeacherGrade | null;
}
export interface ManualGradePayload {
  marks: number;
  feedback?: string | null;
}
export type TeacherAttemptAnswer = Omit<
  StudentAnswer,
  | "textAnswer"
  | "marksAwarded"
  | "feedback"
  | "gradingStatus"
  | "selectedOptions"
  | "isCorrect"
> & {
  isCorrect: Correctness | null;
  textAnswer: string | null;
  marksAwarded: number | null;
  feedback: string | null;
  gradingStatus: GradingStatus | null;
  selectedOptions:
    | {
        optionId: string;
        id: string | null;
        studentExamAnswerId: string | null;
      }[]
    | null;
};
export type TeacherAttempt = Omit<
  StudentExam,
  "answers" | "marksObtained" | "submittedAt" | "isResultsReleased"
> & {
  isResultsReleased: boolean;
  answers: TeacherAttemptAnswer[] | null;
  marksObtained: number | null;
  submittedAt: string | null;
};

export interface ExamGradingSummary {
  examId: string;
  totalSubjectiveAnswers: number;
  pending: number;
  aiSuggestionsReady: number;
  teacherGraded: number;
}

export interface BulkAIEvaluatePayload {
  limit?: number;
  regenerateExisting?: boolean;
}

export interface BulkAIEvaluationItemResult {
  answerId: string;
  studentExamId: string;
  status: "AI_PROPOSAL_CREATED" | "FAILED" | "SKIPPED";
  message?: string | null;
  suggestedMarks?: number | null;
}

export interface BulkAIEvaluateResponse {
  examId: string;
  eligibleCount: number;
  requestedCount: number;
  processedCount: number;
  failedCount: number;
  skippedCount: number;
  remainingCount: number;
  results: BulkAIEvaluationItemResult[];
}

