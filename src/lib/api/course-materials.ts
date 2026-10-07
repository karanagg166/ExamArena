import { api } from "@/lib/axios";
import type {
  CourseMaterialAnswerRequest,
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

export const courseMaterialsApi = {
  askCourseMaterials,
  ask: askCourseMaterials,
};
