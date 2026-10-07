import React from "react";
import { expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import ExamResultsPage from "@/app/(protected)/(teacher-only)/teacher/exams/[examId]/results/page";
import { api } from "@/lib/axios";

vi.mock("next/navigation", () => ({
  useParams: () => ({ examId: "exam1" }),
  useRouter: () => ({ push: vi.fn() }),
}));
vi.mock("@/lib/axios", () => ({ api: { get: vi.fn() } }));
it("links a submitted student's results row directly to their attempt review", async () => {
  vi.mocked(api.get).mockImplementation(async (url) => ({
    data: url.endsWith("/results")
      ? [
          {
            rank: 1,
            attemptId: "attempt1",
            studentId: "student1",
            studentName: "A Student",
            rollNo: "01",
            marksObtained: 0,
            maxMarks: 5,
            percentage: 0,
            status: "SUBMITTED",
            startedAt: "2026-01-01",
            submittedAt: "2026-01-01",
          },
          {
            rank: 2,
            attemptId: "attempt2",
            studentId: "student2",
            studentName: "Another Student",
            rollNo: "02",
            marksObtained: 0,
            maxMarks: 5,
            percentage: 0,
            status: "IN_PROGRESS",
            startedAt: "2026-01-01",
            submittedAt: null,
          },
        ]
      : { id: "exam1", name: "Science", subject: "SCIENCE", maxMarks: 5 },
  }));
  render(<ExamResultsPage />);
  const link = await screen.findByRole("link", { name: "Review answers" });
  expect(link).toHaveAttribute("href", "/teacher/exams/exam1/results/attempt1");
  expect(screen.getAllByRole("link", { name: "Review answers" })).toHaveLength(
    1,
  );
  expect(screen.getByText("Another Student")).toBeInTheDocument();
});
