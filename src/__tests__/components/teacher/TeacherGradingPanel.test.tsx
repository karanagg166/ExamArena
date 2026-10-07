import React, { useState } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { TeacherGradingPanel } from "@/components/teacher/grading/TeacherGradingPanel";
import { gradingApi } from "@/lib/api/grading";
import type {
  AIGradingProposal,
  TeacherAnswerDetail,
  TeacherGrade,
} from "@/types/grading";

vi.mock("@/lib/api/grading", () => ({
  gradingApi: {
    generateAiGrade: vi.fn(),
    acceptAiGrade: vi.fn(),
    updateManualGrade: vi.fn(),
    rejectAiGrade: vi.fn(),
  },
}));
const proposal: AIGradingProposal = {
  answerId: "a1",
  suggestedMarks: 4.5,
  maxMarks: 5,
  rubricBreakdown: [
    {
      criterion: "Definition",
      maxMarks: 5,
      awardedMarks: 4.5,
      justification: "Oxygen omitted.",
    },
  ],
  feedback: "Mention oxygen.",
  confidence: "MEDIUM",
  warnings: ["Reduced grading context"],
};
const answer: TeacherAnswerDetail = {
  id: "a1",
  studentExamId: "at1",
  questionId: "q1",
  questionType: "SHORT_ANSWER",
  questionNumber: 3,
  questionText: "Explain photosynthesis.",
  maxMarks: 5,
  studentAnswer: "Plants use sunlight.\nThey produce glucose.",
  referenceAnswer: "Plants produce glucose and oxygen.",
  gradingRubric: [
    { criterion: "Definition", marks: 5, description: "Define the process" },
  ],
  explanation: null,
  aiProposal: null,
  finalGrade: null,
};
const grade: TeacherGrade = {
  answerId: "a1",
  studentExamId: "at1",
  questionId: "q1",
  marksAwarded: 4.5,
  maxMarks: 5,
  feedback: "Mention oxygen.",
  gradingStatus: "MANUALLY_GRADED",
  gradedBy: "teacher",
  gradedAt: null,
  isCorrect: "PARTIALLY_CORRECT",
};
function Harness({ initial = answer }: { initial?: TeacherAnswerDetail }) {
  const [value, setValue] = useState(initial);
  return <TeacherGradingPanel answer={value} onChange={setValue} />;
}
function enterManual(marks = "4", feedback = "Teacher feedback") {
  fireEvent.click(screen.getByRole("button", { name: "Grade Manually" }));
  fireEvent.change(screen.getByLabelText("Marks / 5"), {
    target: { value: marks },
  });
  fireEvent.change(screen.getByLabelText("Feedback"), {
    target: { value: feedback },
  });
}
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(gradingApi.generateAiGrade).mockResolvedValue(proposal);
  vi.mocked(gradingApi.acceptAiGrade).mockResolvedValue(grade);
  vi.mocked(gradingApi.updateManualGrade).mockResolvedValue(grade);
  vi.mocked(gradingApi.rejectAiGrade).mockResolvedValue({
    answerId: "a1",
    status: "REJECTED",
    message: "Rejected",
  });
});
describe("teacher subjective grading", () => {
  it.each(["SHORT_ANSWER", "ESSAY"] as const)(
    "renders %s with complete student and teacher context",
    (type) => {
      render(<Harness initial={{ ...answer, questionType: type }} />);
      expect(
        screen.getByRole("region", { name: "Student answer text" }).textContent,
      ).toBe(answer.studentAnswer);
      expect(screen.getByText(answer.referenceAnswer!)).toBeInTheDocument();
      expect(screen.getByText("Define the process")).toBeInTheDocument();
      expect(screen.getByText("Definition — 5 marks")).toBeInTheDocument();
    },
  );
  it.each(["MULTIPLE_CHOICE", "MULTIPLE_SELECT", "TRUE_FALSE"] as const)(
    "does not offer AI or manual controls for %s",
    (type) => {
      render(
        <Harness
          initial={{
            ...answer,
            questionType: type,
            finalGrade: { ...grade, gradingStatus: "AUTO_GRADED" },
          }}
        />,
      );
      expect(
        screen.queryByRole("button", { name: /Generate AI/ }),
      ).not.toBeInTheDocument();
      expect(screen.queryByText("Reference Answer")).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: "Grade Manually" }),
      ).not.toBeInTheDocument();
      expect(
        screen.getByRole("region", { name: "Final grade" }),
      ).toHaveTextContent("Automatically graded objective question");
    },
  );
  it("generates a draft with breakdown, confidence, warnings and feedback", async () => {
    render(<Harness />);
    fireEvent.click(screen.getByRole("button", { name: /Generate AI/ }));
    expect(
      await screen.findByText("AI Suggested Score: 4.5 / 5"),
    ).toBeInTheDocument();
    expect(gradingApi.generateAiGrade).toHaveBeenCalledWith("a1");
    expect(screen.getByText("Definition — 4.5 / 5")).toBeInTheDocument();
    expect(screen.getByText("Partial credit")).toBeInTheDocument();
    expect(screen.getByText("Oxygen omitted.")).toBeInTheDocument();
    expect(screen.getByText("Confidence: MEDIUM")).toBeInTheDocument();
    expect(screen.getByText("Reduced grading context")).toBeInTheDocument();
    expect(screen.getByText("Mention oxygen.")).toBeInTheDocument();
    expect(screen.queryByText("Final Grade")).not.toBeInTheDocument();
  });
  it("accepts AI and separates the final teacher grade", async () => {
    render(<Harness initial={{ ...answer, aiProposal: proposal }} />);
    fireEvent.click(
      screen.getByRole("button", { name: "Accept AI Suggestion" }),
    );
    expect(await screen.findByText("Final Grade")).toBeInTheDocument();
    expect(gradingApi.acceptAiGrade).toHaveBeenCalledWith("a1");
    expect(screen.getByText("4.5 / 5")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Accept AI Suggestion" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Generate AI/ }),
    ).not.toBeInTheDocument();
  });
  it("saves modified marks and feedback through the manual endpoint", async () => {
    render(<Harness initial={{ ...answer, aiProposal: proposal }} />);
    fireEvent.click(screen.getByRole("button", { name: "Modify AI Grade" }));
    expect(screen.getByLabelText("Marks / 5")).toHaveValue(4.5);
    expect(screen.getByLabelText("Feedback")).toHaveValue("Mention oxygen.");
    fireEvent.change(screen.getByLabelText("Marks / 5"), {
      target: { value: "4.25" },
    });
    fireEvent.change(screen.getByLabelText("Feedback"), {
      target: { value: "Custom feedback" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save Grade" }));
    await waitFor(() =>
      expect(gradingApi.updateManualGrade).toHaveBeenCalledWith("a1", {
        marks: 4.25,
        feedback: "Custom feedback",
      }),
    );
    expect(gradingApi.acceptAiGrade).not.toHaveBeenCalled();
  });
  it("rejects the proposal without assigning zero or losing manual input", async () => {
    render(<Harness initial={{ ...answer, aiProposal: proposal }} />);
    enterManual("3.5", "Keep draft");
    fireEvent.click(
      screen.getByRole("button", { name: "Reject AI Suggestion" }),
    );
    await waitFor(() =>
      expect(screen.queryByText(/AI Suggested Score/)).not.toBeInTheDocument(),
    );
    expect(gradingApi.rejectAiGrade).toHaveBeenCalledWith("a1");
    expect(screen.getByLabelText("Marks / 5")).toHaveValue(3.5);
    expect(screen.getByLabelText("Feedback")).toHaveValue("Keep draft");
    expect(screen.queryByText("Final Grade")).not.toBeInTheDocument();
    expect(gradingApi.updateManualGrade).not.toHaveBeenCalled();
  });
  it("grades manually without calling AI", async () => {
    render(<Harness />);
    enterManual("0");
    fireEvent.click(screen.getByRole("button", { name: "Save Grade" }));
    expect(await screen.findByText("Final Grade")).toBeInTheDocument();
    expect(gradingApi.updateManualGrade).toHaveBeenCalledWith("a1", {
      marks: 0,
      feedback: "Teacher feedback",
    });
    expect(gradingApi.generateAiGrade).not.toHaveBeenCalled();
  });
  it.each(["", "-1", "5.1"])("blocks invalid marks '%s'", (value) => {
    render(<Harness />);
    enterManual(value);
    expect(screen.getByRole("button", { name: "Save Grade" })).toBeDisabled();
    expect(gradingApi.updateManualGrade).not.toHaveBeenCalled();
  });
  it("keeps manual grading and drafts available after provider failure", async () => {
    vi.mocked(gradingApi.generateAiGrade).mockRejectedValue({
      isAxiosError: true,
      response: { status: 502 },
    });
    render(<Harness />);
    enterManual("3.5", "Keep feedback");
    fireEvent.click(screen.getByRole("button", { name: /Generate AI/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "AI grading is currently unavailable",
    );
    expect(screen.getByLabelText("Marks / 5")).toHaveValue(3.5);
    expect(screen.getByLabelText("Feedback")).toHaveValue("Keep feedback");
    expect(
      screen.getByRole("region", { name: "Student answer text" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Save Grade" }));
    expect(await screen.findByText("Final Grade")).toBeInTheDocument();
  });
  it.each([
    [401, "Your session has expired"],
    [403, "You do not have permission"],
    [400, "Grading context missing"],
    [422, "AI result failed validation"],
  ])(
    "shows the API error for status %s without removing the answer",
    async (status, message) => {
      vi.mocked(gradingApi.generateAiGrade).mockRejectedValue({
        isAxiosError: true,
        response: { status, data: { detail: message } },
      });
      render(<Harness />);
      fireEvent.click(screen.getByRole("button", { name: /Generate AI/ }));
      expect(await screen.findByRole("alert")).toHaveTextContent(
        String(message),
      );
      expect(
        screen.getByRole("region", { name: "Student answer text" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "Grade Manually" }),
      ).toBeEnabled();
    },
  );
  it("preserves edited values when saving fails and allows a retry", async () => {
    vi.mocked(gradingApi.updateManualGrade).mockRejectedValueOnce({
      isAxiosError: true,
      response: { status: 422, data: { detail: "Grade validation failed" } },
    });
    render(<Harness />);
    enterManual("3.25", "Keep my edits");
    fireEvent.click(screen.getByRole("button", { name: "Save Grade" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Grade validation failed",
    );
    expect(screen.getByLabelText("Marks / 5")).toHaveValue(3.25);
    expect(screen.getByLabelText("Feedback")).toHaveValue("Keep my edits");
    fireEvent.click(screen.getByRole("button", { name: "Save Grade" }));
    expect(await screen.findByText("Final Grade")).toBeInTheDocument();
  });
  it("explains missing context and permits manual grading", () => {
    render(
      <Harness
        initial={{ ...answer, referenceAnswer: null, gradingRubric: null }}
      />,
    );
    expect(screen.getByRole("button", { name: /Generate AI/ })).toBeDisabled();
    expect(screen.getByRole("note")).toHaveTextContent(
      "Manual grading is still available",
    );
    enterManual();
    expect(screen.getByRole("button", { name: "Save Grade" })).toBeEnabled();
  });
  it("prevents duplicate generation while in flight", async () => {
    let resolve!: (value: AIGradingProposal) => void;
    vi.mocked(gradingApi.generateAiGrade).mockReturnValue(
      new Promise((r) => {
        resolve = r;
      }),
    );
    render(<Harness />);
    const button = screen.getByRole("button", { name: /Generate AI/ });
    fireEvent.click(button);
    fireEvent.click(button);
    expect(button).toBeDisabled();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Generating grading suggestion",
    );
    expect(gradingApi.generateAiGrade).toHaveBeenCalledTimes(1);
    resolve(proposal);
    await screen.findByText("AI Suggested Score: 4.5 / 5");
  });
});

it("can leave manual editing to accept an AI proposal", async () => {
  render(<Harness initial={{ ...answer, aiProposal: proposal }} />);
  enterManual();
  expect(
    screen.getByRole("button", { name: "Accept AI Suggestion" }),
  ).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Cancel editing" }));
  fireEvent.click(screen.getByRole("button", { name: "Accept AI Suggestion" }));
  expect(await screen.findByText("Final Grade")).toBeInTheDocument();
});
