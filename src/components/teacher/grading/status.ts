import { isAxiosError } from "axios";
import { getErrorMessage } from "@/lib/error";
import type { QuestionType } from "@/types/question";

export const isSubjective = (type: QuestionType) =>
  type === "SHORT_ANSWER" || type === "ESSAY";
export function gradingStatusLabel(status: string | null | undefined) {
  switch (status) {
    case "MANUALLY_GRADED":
      return "Teacher graded";
    case "AUTO_GRADED":
      return "Automatically graded objective question";
    default:
      return "Pending teacher review";
  }
}
export function gradingError(error: unknown, ai = false) {
  if (isAxiosError(error)) {
    if (error.response?.status === 401)
      return "Your session has expired. Sign in again to continue grading.";
    if (error.response?.status === 403)
      return "You do not have permission to grade this submission.";
    if (ai && (!error.response || error.response.status >= 500)) {
      return "AI grading is currently unavailable. You can still grade this answer manually.";
    }
  }
  return `${getErrorMessage(error)}${ai ? " Manual grading is still available." : ""}`;
}
