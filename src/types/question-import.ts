import { QuestionType } from "./question";

export type QuestionImportStatus =
  | "UPLOADED"
  | "PROCESSING"
  | "NEEDS_REVIEW"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export type QuestionImportSourceType =
  | "PDF_TEXT"
  | "PDF_SCANNED"
  | "IMAGE"
  | "UNKNOWN";

export type ExtractedConfidence = "HIGH" | "MEDIUM" | "LOW";

export interface ExtractedOption {
  label?: string | null;
  text: string;
  is_correct?: boolean | null;
}

export interface ExtractedQuestion {
  question_number?: string | null;
  question_type: QuestionType | "UNKNOWN";
  text: string;
  marks?: number | null;
  options: ExtractedOption[];
  section?: string | null;
  instructions?: string | null;
  image_reference?: string | null;
  confidence: ExtractedConfidence;
  warnings: string[];
}

export interface QuestionImport {
  id: string;
  examId: string;
  teacherId: string;
  originalFileName: string;
  fileType: string;
  fileSize: number;
  status: QuestionImportStatus;
  sourceType: QuestionImportSourceType;
  errorMessage?: string | null;
  errorCategory?: string | null;
  createdAt: string;
  updatedAt: string;
  completedAt?: string | null;
  confirmedAt?: string | null;
  questionCount?: number;
  title?: string | null;
  subject?: string | null;
  questions?: ExtractedQuestion[] | null;
  warnings: string[];
}

export interface QuestionImportListItem {
  id: string;
  examId: string;
  teacherId: string;
  originalFileName: string;
  fileType: string;
  fileSize: number;
  status: QuestionImportStatus;
  sourceType: QuestionImportSourceType;
  questionCount: number;
  createdAt: string;
  updatedAt: string;
  completedAt?: string | null;
  confirmedAt?: string | null;
}

export interface QuestionImportConfirmResponse {
  id: string;
  examId: string;
  status: QuestionImportStatus;
  createdQuestionsCount: number;
  confirmedAt: string;
}
