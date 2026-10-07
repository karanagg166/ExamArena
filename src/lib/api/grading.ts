import { api } from "@/lib/axios";
import type {
  AIGradingProposal,
  ManualGradePayload,
  TeacherAnswerDetail,
  TeacherAttempt,
  TeacherGrade,
} from "@/types/grading";

const answerPath = (id: string) =>
  `/api/v1/student-answers/${encodeURIComponent(id)}`;
export const gradingApi = {
  async getAttempt(id: string) {
    return (
      await api.get<TeacherAttempt>(
        `/api/v1/attempts/${encodeURIComponent(id)}`,
      )
    ).data;
  },
  async getAnswer(id: string) {
    return (await api.get<TeacherAnswerDetail>(answerPath(id))).data;
  },
  async generateAiGrade(id: string) {
    return (await api.post<AIGradingProposal>(`${answerPath(id)}/ai-grade`))
      .data;
  },
  async acceptAiGrade(id: string) {
    return (await api.post<TeacherGrade>(`${answerPath(id)}/grade/accept-ai`))
      .data;
  },
  async updateManualGrade(id: string, payload: ManualGradePayload) {
    return (await api.patch<TeacherGrade>(`${answerPath(id)}/grade`, payload))
      .data;
  },
  async rejectAiGrade(id: string) {
    return (
      await api.post<{ answerId: string; status: "REJECTED"; message: string }>(
        `${answerPath(id)}/grade/reject-ai`,
      )
    ).data;
  },
};
