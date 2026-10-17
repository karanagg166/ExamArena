export type CourseMaterialStatus = "PROCESSING" | "READY" | "FAILED";
export type CourseMaterialDocumentType = "SYLLABUS" | "TEXTBOOK" | "NOTES" | "ASSIGNMENT" | "OTHER";

export interface CourseMaterialItem {
  id: string;
  schoolId: string;
  subject: string;
  classId?: string | null;
  uploadedBy: string;
  title: string;
  description?: string | null;
  originalFileName: string;
  fileSize: number;
  mimeType: string;
  documentType: CourseMaterialDocumentType;
  searchSphereDocumentId?: string | null;
  searchSphereCollectionId: string;
  status: CourseMaterialStatus;
  processingError?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface CourseMaterialListResponse {
  total: number;
  items: CourseMaterialItem[];
}

export interface CourseMaterialStatusRefreshResponse {
  material_id: string;
  status: CourseMaterialStatus;
  search_sphere_document_id?: string | null;
  processing_error?: string | null;
}

export interface GroundedCitation {
  citationNumber: number;
  fileName?: string | null;
  title?: string | null;
  pageNumber?: number | null;
  textSnippet: string;
  materialId?: string | null;
  documentType?: string | null;
}

export interface GroundedAnswer {
  answer: string;
  citations: GroundedCitation[];
  retrievedChunkCount?: number;
  warnings?: string[];
  durationMs?: number;
}

export interface CourseMaterialAnswerRequest {
  query: string;
  subject: string;
  classId?: string;
  documentType?: string;
  limit?: number;
}

