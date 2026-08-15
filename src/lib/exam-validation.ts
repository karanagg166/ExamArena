import type { ExamCreate } from "@/types";

const SECTION_PATTERN = /^Section [A-Z]$/;

/**
 * Validates an exam payload before submission.
 * Returns a human-readable error string, or null if completely valid.
 * NOTE: Past scheduledAt date/time is intentionally allowed.
 */
export function validateExam(exam: Partial<ExamCreate>): string | null {
  if (!exam.name?.trim()) return "Exam title is required.";
  if (!exam.description?.trim()) return "Description is required.";
  if (!exam.scheduledAt) return "Scheduled date and time is required.";
  if ((exam.duration ?? 0) < 5) return "Duration must be at least 5 minutes.";
  if (!exam.questions || exam.questions.length === 0)
    return "Add at least one question.";

  for (let i = 0; i < exam.questions.length; i++) {
    const q = exam.questions[i];
    const qNum = q.questionNumber ?? i + 1;
    const sec = q.section?.trim() || "Section A";

    if (!q.text?.trim()) {
      return `Question ${qNum} in ${sec} cannot be empty. Please enter question prompt.`;
    }

    if (!SECTION_PATTERN.test(sec)) {
      return `Invalid section "${sec}" for Question ${qNum}. Must be "Section A", "Section B", etc.`;
    }

    if (!q.marks || q.marks < 1) {
      return `Question ${qNum} in ${sec} must have marks greater than 0.`;
    }

    const needsOptions =
      q.questionType === "MULTIPLE_CHOICE" ||
      q.questionType === "TRUE_FALSE" ||
      q.questionType === "MULTIPLE_SELECT";

    if (needsOptions) {
      if (!q.options || q.options.length === 0) {
        return `Question ${qNum} in ${sec} must have options.`;
      }

      if (q.questionType === "TRUE_FALSE" && q.options.length !== 2) {
        return `Question ${qNum} in ${sec} (True/False) must have exactly 2 options.`;
      }

      for (let j = 0; j < q.options.length; j++) {
        if (!q.options[j].text?.trim()) {
          return `Option ${j + 1} for Question ${qNum} in ${sec} cannot be empty.`;
        }
      }

      if (!q.options.some((o) => o.isCorrect)) {
        return `Question ${qNum} in ${sec} must have at least one correct option selected.`;
      }
    }
  }

  return null;
}

/**
 * Computes total marks from all questions. This value should be sent
 * as `maxMarks` to keep frontend and backend in sync.
 */
export function computeMaxMarks(questions: { marks?: number }[]): number {
  return questions.reduce((sum, q) => sum + (q.marks ?? 0), 0);
}
