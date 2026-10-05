import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ExamForm } from "@/components/exam/ExamForm";
import ExamResultPage from "@/app/(protected)/(student-only)/student/exams/[examId]/result/page";
import { api } from "@/lib/axios";

vi.mock("next/navigation", () => ({
  useParams: () => ({ examId: "exam-test-123" }),
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

vi.mock("@/lib/axios", () => ({
  api: {
    get: vi.fn(),
    patch: vi.fn(),
    post: vi.fn(),
  },
}));

describe("ExamForm Password Configuration", () => {
  const baseExam = {
    name: "Midterm Physics",
    description: "Introductory Physics Exam",
    scheduledAt: "2026-10-15T09:00:00Z",
    duration: 60,
    type: "MIDTERM" as const,
    maxMarks: 100,
    isPublished: true,
    isPublic: false,
    hasAccessPassword: true,
    accessPassword: "",
  };

  it("renders empty password input and 'Password configured' badge for protected exam", () => {
    const handleChange = vi.fn();
    render(<ExamForm exam={baseExam} onChange={handleChange} />);

    // Badge indicates password is configured
    expect(screen.getByText("Password configured")).toBeDefined();

    // Password input field exists and has empty value
    const passwordInput = screen.getByLabelText(
      /Exam Access Password \/ Secret Key/i
    ) as HTMLInputElement;
    expect(passwordInput.value).toBe("");
    expect(passwordInput.placeholder).toContain("Leave blank to keep existing password");

    // Must not display any bcrypt hash
    expect(screen.queryByText(/\$2[aby]\$/)).toBeNull();
  });

  it("calls onChange with isPublic: true when switching to Public Exam", () => {
    const handleChange = vi.fn();
    render(<ExamForm exam={baseExam} onChange={handleChange} />);

    const publicBtn = screen.getByRole("button", { name: /^Public Exam$/i });
    fireEvent.click(publicBtn);

    expect(handleChange).toHaveBeenCalledWith({ isPublic: true });
  });

  it("calls onChange with isPublic: false when switching to Password Protected", () => {
    const handleChange = vi.fn();
    render(
      <ExamForm
        exam={{ ...baseExam, isPublic: true, hasAccessPassword: false }}
        onChange={handleChange}
      />
    );

    const protectedBtn = screen.getByRole("button", {
      name: /^Password Protected$/i,
    });
    fireEvent.click(protectedBtn);

    expect(handleChange).toHaveBeenCalledWith({ isPublic: false });
  });
});

describe("ExamResultPage Results Visibility", () => {
  const mockExam = {
    id: "exam-test-123",
    name: "Final Physics Paper",
    maxMarks: 100,
    isResultsReleased: false,
    questions: [
      {
        id: "q-1",
        text: "What is Newton's first law?",
        marks: 10,
        questionType: "MULTIPLE_CHOICE",
        explanation: "Law of inertia",
        options: [
          { id: "opt-1", text: "Inertia", isCorrect: true },
          { id: "opt-2", text: "Action-Reaction", isCorrect: false },
        ],
      },
    ],
  };

  const mockAttempt = {
    id: "attempt-456",
    examId: "exam-test-123",
    studentId: "student-789",
    status: "EVALUATED",
    marksObtained: 85,
    isResultsReleased: false,
    answers: [
      {
        id: "ans-1",
        questionId: "q-1",
        isCorrect: "FULLY_CORRECT",
        marksAwarded: 10,
        selectedOptions: [{ optionId: "opt-1" }],
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("hides score, percentage, and answer key when results are not released", async () => {
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url === "/api/v1/exams/exam-test-123") {
        return Promise.resolve({ data: { ...mockExam, isResultsReleased: false } });
      }
      if (url === "/api/v1/exams/student") {
        return Promise.resolve({
          data: [{ id: "exam-test-123", attemptId: "attempt-456" }],
        });
      }
      if (url === "/api/v1/attempts/attempt-456") {
        return Promise.resolve({
          data: { ...mockAttempt, isResultsReleased: false, marksObtained: null },
        });
      }
      return Promise.reject(new Error("Not found"));
    });

    render(<ExamResultPage />);

    await waitFor(() => {
      expect(screen.getByText("Exam Submitted Successfully")).toBeDefined();
    });

    expect(
      screen.getByText(
        /Results and full answer keys are currently pending teacher release/i
      )
    ).toBeDefined();

    // Sensitive score and answer breakdown must NOT be displayed
    expect(screen.queryByText("Score Obtained")).toBeNull();
    expect(screen.queryByText("Percentage")).toBeNull();
    expect(screen.queryByText(/Answer Key & Explanations/i)).toBeNull();
  });

  it("reveals score, percentage, and answer key when results are released", async () => {
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url === "/api/v1/exams/exam-test-123") {
        return Promise.resolve({ data: { ...mockExam, isResultsReleased: true } });
      }
      if (url === "/api/v1/exams/student") {
        return Promise.resolve({
          data: [{ id: "exam-test-123", attemptId: "attempt-456" }],
        });
      }
      if (url === "/api/v1/attempts/attempt-456") {
        return Promise.resolve({
          data: { ...mockAttempt, isResultsReleased: true, marksObtained: 85 },
        });
      }
      return Promise.reject(new Error("Not found"));
    });

    render(<ExamResultPage />);

    await waitFor(() => {
      expect(screen.getByText("Exam Results Released")).toBeDefined();
    });

    expect(screen.getByText("Score Obtained")).toBeDefined();
    expect(screen.getByText("Percentage")).toBeDefined();
    expect(screen.getByText(/\/ 100/)).toBeDefined();
    expect(screen.getByText("85.0%")).toBeDefined();
    expect(screen.getByText(/Answer Key & Explanations/i)).toBeDefined();
    expect(screen.getByText(/Fully Correct \(\+10 Marks\)/i)).toBeDefined();
  });
});
