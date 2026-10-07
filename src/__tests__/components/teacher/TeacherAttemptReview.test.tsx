import React from "react";
import { beforeEach, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { TeacherAttemptReview } from "@/components/teacher/grading/TeacherAttemptReview";
import TeacherSubmissionPage from "@/app/(protected)/(teacher-only)/teacher/exams/[examId]/results/[attemptId]/page";
import { api } from "@/lib/axios";
import { gradingApi } from "@/lib/api/grading";
import type { TeacherAnswerDetail, TeacherAttempt } from "@/types/grading";

const session = vi.hoisted(() => ({
  user: { role: "TEACHER" } as { role: string } | null,
}));
vi.mock("@/stores/useAuthStore", () => ({
  useAuthStore: (selector: (state: typeof session) => unknown) =>
    selector(session),
}));
vi.mock("next/navigation", () => ({
  useParams: () => ({ examId: "ex", attemptId: "at" }),
}));
vi.mock("@/lib/axios", () => ({ api: { get: vi.fn() } }));
vi.mock("@/lib/api/grading", () => ({
  gradingApi: {
    getAttempt: vi.fn(),
    getAnswer: vi.fn(),
    generateAiGrade: vi.fn(),
    acceptAiGrade: vi.fn(),
    updateManualGrade: vi.fn(),
    rejectAiGrade: vi.fn(),
  },
}));
const attempt: TeacherAttempt = {
  id: "at",
  examId: "ex",
  studentId: "st",
  status: "SUBMITTED",
  isResultsReleased: false,
  marksObtained: 1,
  startedAt: "2026-01-01",
  submittedAt: "2026-01-01",
  answers: [
    {
      id: "a1",
      studentExamId: "at",
      questionId: "q1",
      questionType: "MULTIPLE_CHOICE",
      gradingStatus: "AUTO_GRADED",
      isCorrect: "FULLY_CORRECT",
      marksAwarded: 1,
      feedback: null,
      textAnswer: null,
      selectedOptions: [
        { optionId: "opt", id: null, studentExamAnswerId: null },
      ],
      createdAt: "",
      updatedAt: "",
    },
    {
      id: "a2",
      studentExamId: "at",
      questionId: "q2",
      questionType: "ESSAY",
      gradingStatus: "PENDING",
      isCorrect: null,
      marksAwarded: null,
      feedback: null,
      textAnswer: "Essay text",
      selectedOptions: [],
      createdAt: "",
      updatedAt: "",
    },
  ],
};
const subjective: TeacherAnswerDetail = {
  id: "a2",
  studentExamId: "at",
  questionId: "q2",
  questionType: "ESSAY",
  questionNumber: 2,
  questionText: "Explain",
  maxMarks: 5,
  studentAnswer: "Essay text",
  referenceAnswer: "Teacher reference",
  gradingRubric: [{ criterion: "Content", marks: 5 }],
  explanation: null,
  aiProposal: null,
  finalGrade: null,
};
beforeEach(() => {
  vi.resetAllMocks();
  session.user = { role: "TEACHER" };
  vi.mocked(api.get).mockResolvedValue({
    data: {
      name: "Science",
      questions: [
        {
          id: "q1",
          questionNumber: 1,
          options: [{ id: "opt", text: "Selected answer" }],
        },
        { id: "q2", questionNumber: 2 },
      ],
    },
  });
  vi.mocked(gradingApi.getAttempt).mockResolvedValue(attempt);
  vi.mocked(gradingApi.getAnswer).mockImplementation(async (id) =>
    id === "a2"
      ? subjective
      : {
          ...subjective,
          id: "a1",
          questionId: "q1",
          questionType: "MULTIPLE_CHOICE",
          questionNumber: 1,
          studentAnswer: null,
          finalGrade: {
            answerId: "a1",
            studentExamId: "at",
            questionId: "q1",
            marksAwarded: 1,
            maxMarks: 1,
            feedback: null,
            gradingStatus: "AUTO_GRADED",
            gradedBy: null,
            gradedAt: null,
            isCorrect: "FULLY_CORRECT",
          },
        },
  );
});
it("opens the exact attempt, navigates answers and updates subjective progress after saving", async () => {
  vi.mocked(gradingApi.updateManualGrade).mockResolvedValue({
    answerId: "a2",
    studentExamId: "at",
    questionId: "q2",
    marksAwarded: 3.5,
    maxMarks: 5,
    feedback: "Good",
    gradingStatus: "MANUALLY_GRADED",
    gradedAt: null,
    gradedBy: "t",
    isCorrect: "PARTIALLY_CORRECT",
  });
  render(<TeacherAttemptReview examId="ex" attemptId="at" />);
  expect(
    await screen.findByText("Selected answer", {}, { timeout: 5000 }),
  ).toBeInTheDocument();
  expect(gradingApi.getAttempt).toHaveBeenCalledWith("at");
  expect(
    screen.queryByRole("button", { name: /Generate AI/ }),
  ).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Next Question" }));
  expect(await screen.findByText("Essay text")).toBeInTheDocument();
  expect(screen.getByText("Teacher reference")).toBeInTheDocument();
  expect(
    screen.getByText("Subjective grading: 0 of 1 answers graded"),
  ).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Grade Manually" }));
  fireEvent.change(screen.getByLabelText("Marks / 5"), {
    target: { value: "3.5" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save Grade" }));
  expect(
    await screen.findByText("Subjective grading: 1 of 1 answers graded"),
  ).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Next Question" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Previous Question" }));
  expect(
    await screen.findByText("Selected answer", {}, { timeout: 5000 }),
  ).toBeInTheDocument();
});
it("does not fetch teacher context for a student visiting the teacher route", () => {
  session.user = { role: "STUDENT" };
  render(<TeacherSubmissionPage />);
  expect(screen.getByRole("alert")).toHaveTextContent(
    "Teacher access required",
  );
  expect(gradingApi.getAttempt).not.toHaveBeenCalled();
  expect(gradingApi.getAnswer).not.toHaveBeenCalled();
  expect(screen.queryByText("Teacher reference")).not.toBeInTheDocument();
});
it("rejects a route pointing to an attempt in another exam", async () => {
  vi.mocked(gradingApi.getAttempt).mockResolvedValue({
    ...attempt,
    examId: "other",
  });
  render(<TeacherAttemptReview examId="ex" attemptId="at" />);
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "does not belong to this exam",
  );
  expect(gradingApi.getAnswer).not.toHaveBeenCalled();
});
it("does not expose grading actions for an attempt still in progress", async () => {
  vi.mocked(gradingApi.getAttempt).mockResolvedValue({
    ...attempt,
    status: "IN_PROGRESS",
  });
  render(<TeacherAttemptReview examId="ex" attemptId="at" />);
  expect(
    await screen.findByText(/This attempt has not been submitted/),
  ).toBeInTheDocument();
  expect(gradingApi.getAnswer).not.toHaveBeenCalled();
});
