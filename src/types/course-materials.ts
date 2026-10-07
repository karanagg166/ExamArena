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
