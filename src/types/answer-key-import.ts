export type AnswerKeyImportStatus =
  | "UPLOADED"
  | "PROCESSING"
  | "NEEDS_REVIEW"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export type AnswerKeyImportSourceType =
  | "PDF_TEXT"
  | "PDF_SCANNED"
  | "IMAGE"
  | "UNKNOWN";

export type MatchStatus = "MATCHED" | "AMBIGUOUS" | "UNMATCHED";

export interface RubricCriterion {
  criterion: string;
  marks: number;
  description?: string | null;
}

export interface MatchedAnswer {
  question_reference: string;
  question_text_snippet?: string | null;
  selected_option?: string | null;
  selected_option_text?: string | null;
  reference_answer?: string | null;
  explanation?: string | null;
  rubric: RubricCriterion[];
  marks?: number | null;
  confidence: "HIGH" | "MEDIUM" | "LOW";
  warnings: string[];
  status: MatchStatus;
  matched_question_id?: string | null;
  matched_question_number?: number | null;
  matched_question_text?: string | null;
  matched_question_type?: string | null;
  matched_option_id?: string | null;
  match_confidence: number;
  match_reason?: string | null;
  candidate_question_ids: string[];
}

export interface AnswerKeyImport {
  id: string;
  examId: string;
  teacherId: string;
  originalFileName: string;
  fileType: string;
  fileSize: number;
  status: AnswerKeyImportStatus;
  sourceType: AnswerKeyImportSourceType;
  errorMessage?: string | null;
  errorCategory?: string | null;
  createdAt: string;
  updatedAt: string;
  completedAt?: string | null;
  confirmedAt?: string | null;
  matchedCount: number;
  ambiguousCount: number;
  unmatchedCount: number;
  totalAnswers: number;
  title?: string | null;
  examReference?: string | null;
  answers?: MatchedAnswer[] | null;
  warnings: string[];
  storageProvider?: string | null;
  storageUrl?: string | null;
}

export interface AnswerKeyImportListItem {
  id: string;
  examId: string;
  teacherId: string;
  originalFileName: string;
  fileType: string;
  fileSize: number;
  status: AnswerKeyImportStatus;
  sourceType: AnswerKeyImportSourceType;
  matchedCount: number;
  totalAnswers: number;
  createdAt: string;
  updatedAt: string;
  completedAt?: string | null;
  confirmedAt?: string | null;
}

export interface AnswerKeyImportConfirmResponse {
  id: string;
  examId: string;
  status: AnswerKeyImportStatus;
  updatedQuestionsCount: number;
  confirmedAt: string;
}
