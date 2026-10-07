import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { BulkGradingCard } from "@/components/teacher/grading/BulkGradingCard";
import { gradingApi } from "@/lib/api/grading";
import type { BulkAIEvaluateResponse, ExamGradingSummary } from "@/types/grading";

vi.mock("@/lib/api/grading", () => ({
  gradingApi: {
    getExamGradingSummary: vi.fn(),
    bulkEvaluatePendingAnswers: vi.fn(),
  },
}));

describe("BulkGradingCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders objective-only exam state and hides bulk button when no subjective answers exist", async () => {
    const summary: ExamGradingSummary = {
      examId: "exam-1",
      totalSubjectiveAnswers: 0,
      pending: 0,
      aiSuggestionsReady: 0,
      teacherGraded: 0,
    };
    vi.mocked(gradingApi.getExamGradingSummary).mockResolvedValue(summary);

    render(<BulkGradingCard examId="exam-1" />);

    expect(
      await screen.findByText(/No subjective answers require grading/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Evaluate Pending with AI/i }),
    ).not.toBeInTheDocument();
  });

  it("renders grading summary cards with correct counts", async () => {
    const summary: ExamGradingSummary = {
      examId: "exam-1",
      totalSubjectiveAnswers: 42,
      pending: 22,
      aiSuggestionsReady: 10,
      teacherGraded: 10,
    };
    vi.mocked(gradingApi.getExamGradingSummary).mockResolvedValue(summary);

    render(<BulkGradingCard examId="exam-1" />);

    expect(await screen.findByText("42")).toBeInTheDocument();
    expect(screen.getByText("22")).toBeInTheDocument();
    expect(screen.getAllByText("10")).toHaveLength(2);
    expect(
      screen.getByRole("button", { name: /Evaluate Pending with AI/i }),
    ).toBeInTheDocument();
  });

  it("opens confirmation dialog when Evaluate Pending with AI is clicked", async () => {
    const summary: ExamGradingSummary = {
      examId: "exam-1",
      totalSubjectiveAnswers: 15,
      pending: 10,
      aiSuggestionsReady: 2,
      teacherGraded: 3,
    };
    vi.mocked(gradingApi.getExamGradingSummary).mockResolvedValue(summary);

    render(<BulkGradingCard examId="exam-1" />);

    const evalBtn = await screen.findByRole("button", {
      name: /Evaluate Pending with AI/i,
    });
    fireEvent.click(evalBtn);

    expect(
      screen.getByText(/Confirm AI Evaluation Batch/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Generate AI grading suggestions for up to 20 pending subjective answers/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Start AI Evaluation/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Cancel/i })).toBeInTheDocument();
  });

  it("calls bulk evaluation API with confirmation and displays success feedback", async () => {
    const initialSummary: ExamGradingSummary = {
      examId: "exam-1",
      totalSubjectiveAnswers: 20,
      pending: 20,
      aiSuggestionsReady: 0,
      teacherGraded: 0,
    };
    const updatedSummary: ExamGradingSummary = {
      examId: "exam-1",
      totalSubjectiveAnswers: 20,
      pending: 2,
      aiSuggestionsReady: 18,
      teacherGraded: 0,
    };
    const bulkResponse: BulkAIEvaluateResponse = {
      examId: "exam-1",
      eligibleCount: 20,
      requestedCount: 20,
      processedCount: 18,
      failedCount: 2,
      skippedCount: 0,
      remainingCount: 2,
      results: [],
    };

    vi.mocked(gradingApi.getExamGradingSummary)
      .mockResolvedValueOnce(initialSummary)
      .mockResolvedValueOnce(updatedSummary);
    vi.mocked(gradingApi.bulkEvaluatePendingAnswers).mockResolvedValue(
      bulkResponse,
    );

    const onEvaluatedMock = vi.fn();
    render(
      <BulkGradingCard examId="exam-1" onGradingEvaluated={onEvaluatedMock} />,
    );

    const evalBtn = await screen.findByRole("button", {
      name: /Evaluate Pending with AI/i,
    });
    fireEvent.click(evalBtn);

    const startBtn = screen.getByRole("button", {
      name: /Start AI Evaluation/i,
    });
    fireEvent.click(startBtn);

    await waitFor(() => {
      expect(gradingApi.bulkEvaluatePendingAnswers).toHaveBeenCalledWith(
        "exam-1",
        { limit: 20, regenerateExisting: false },
      );
    });

    expect(
      await screen.findByText(/18 AI grading suggestions created/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/2 answers could not be evaluated/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/2 answers remain pending/i),
    ).toBeInTheDocument();

    expect(onEvaluatedMock).toHaveBeenCalledTimes(1);
  });

  it("allows resuming remaining pending answers", async () => {
    const initialSummary: ExamGradingSummary = {
      examId: "exam-1",
      totalSubjectiveAnswers: 30,
      pending: 10,
      aiSuggestionsReady: 15,
      teacherGraded: 5,
    };
    const finalSummary: ExamGradingSummary = {
      examId: "exam-1",
      totalSubjectiveAnswers: 30,
      pending: 0,
      aiSuggestionsReady: 25,
      teacherGraded: 5,
    };
    const bulkResponse: BulkAIEvaluateResponse = {
      examId: "exam-1",
      eligibleCount: 10,
      requestedCount: 20,
      processedCount: 10,
      failedCount: 0,
      skippedCount: 0,
      remainingCount: 0,
      results: [],
    };

    vi.mocked(gradingApi.getExamGradingSummary)
      .mockResolvedValueOnce(initialSummary)
      .mockResolvedValueOnce(finalSummary);
    vi.mocked(gradingApi.bulkEvaluatePendingAnswers).mockResolvedValue(
      bulkResponse,
    );

    render(<BulkGradingCard examId="exam-1" />);

    const evalBtn = await screen.findByRole("button", {
      name: /Evaluate Pending with AI/i,
    });
    fireEvent.click(evalBtn);

    const startBtn = screen.getByRole("button", {
      name: /Start AI Evaluation/i,
    });
    fireEvent.click(startBtn);

    expect(
      await screen.findByText(/10 AI grading suggestions created/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/0 answers remain pending/i)).toBeInTheDocument();
  });
});
