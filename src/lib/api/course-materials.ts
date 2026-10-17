import { api } from "@/lib/axios";
import type {
  CourseMaterialAnswerRequest,
  CourseMaterialItem,
  CourseMaterialListResponse,
  CourseMaterialStatusRefreshResponse,
  GroundedAnswer,
} from "@/types/course-materials";

export async function askCourseMaterials(
  payload: CourseMaterialAnswerRequest,
): Promise<GroundedAnswer> {
  const response = await api.post<GroundedAnswer>(
    "/api/v1/course-materials/answer",
    payload,
  );
  return response.data;
}

export async function listCourseMaterials(params?: {
  subject?: string;
  class_id?: string;
  status?: string;
  document_type?: string;
  limit?: number;
  offset?: number;
}): Promise<CourseMaterialListResponse> {
  const response = await api.get<CourseMaterialListResponse>(
    "/api/v1/course-materials",
    { params },
  );
  return response.data;
}

export async function uploadCourseMaterial(
  formData: FormData,
): Promise<CourseMaterialItem> {
  const response = await api.post<CourseMaterialItem>(
    "/api/v1/course-materials/upload",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );
  return response.data;
}

export async function refreshCourseMaterialStatus(
  materialId: string,
): Promise<CourseMaterialStatusRefreshResponse> {
  const response = await api.post<CourseMaterialStatusRefreshResponse>(
    `/api/v1/course-materials/${materialId}/refresh-status`,
  );
  return response.data;
}

export async function deleteCourseMaterial(
  materialId: string,
): Promise<{ success: boolean; message: string }> {
  const response = await api.delete<{ success: boolean; message: string }>(
    `/api/v1/course-materials/${materialId}`,
  );
  return response.data;
}

export const courseMaterialsApi = {
  askCourseMaterials,
  ask: askCourseMaterials,
  listCourseMaterials,
  list: listCourseMaterials,
  uploadCourseMaterial,
  upload: uploadCourseMaterial,
  refreshCourseMaterialStatus,
  refreshStatus: refreshCourseMaterialStatus,
  deleteCourseMaterial,
  delete: deleteCourseMaterial,
};

