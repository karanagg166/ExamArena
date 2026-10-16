import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  ExamResultsTable,
  type StudentScoreboardResult,
} from "@/components/exam/ExamResultsTable";

const mockResults: StudentScoreboardResult[] = [
  {
    rank: 1,
    attemptId: "att_1",
    studentId: "stu_1",
    studentName: "Aarav Patel",
    rollNo: "CS101",
    marksObtained: 95,
    maxMarks: 100,
    percentage: 95,
    status: "EVALUATED",
    startedAt: "2026-01-01T10:00:00Z",
    submittedAt: "2026-01-01T11:00:00Z",
  },
  {
    rank: 2,
    attemptId: "att_2",
    studentId: "stu_2",
    studentName: "Bhavna Gupta",
    rollNo: "CS102",
    marksObtained: 70,
    maxMarks: 100,
    percentage: 70,
    status: "EVALUATED",
    startedAt: "2026-01-01T10:00:00Z",
    submittedAt: "2026-01-01T11:15:00Z",
  },
  {
    rank: 3,
    attemptId: "att_3",
    studentId: "stu_3",
    studentName: "Chirag Singh",
    rollNo: "CS103",
    marksObtained: 35,
    maxMarks: 100,
    percentage: 35,
    status: "EVALUATED",
    startedAt: "2026-01-01T10:00:00Z",
    submittedAt: "2026-01-01T11:30:00Z",
  },
];

describe("Component: ExamResultsTable", () => {
  it("renders leaderboard rows with student names and ranks", () => {
    render(<ExamResultsTable results={mockResults} />);

    expect(screen.getByText("Aarav Patel")).toBeInTheDocument();
    expect(screen.getByText("Bhavna Gupta")).toBeInTheDocument();
    expect(screen.getByText("Chirag Singh")).toBeInTheDocument();
    expect(screen.getByText("CS101")).toBeInTheDocument();
  });

  it("filters students based on search input", () => {
    render(<ExamResultsTable results={mockResults} />);

    const searchInput = screen.getByPlaceholderText(/search candidates/i);
    fireEvent.change(searchInput, { target: { value: "Aarav" } });

    expect(screen.getByText("Aarav Patel")).toBeInTheDocument();
    expect(screen.queryByText("Bhavna Gupta")).not.toBeInTheDocument();
  });

  it("calls onViewAttempt when review button is clicked", () => {
    const handleView = vi.fn();
    render(<ExamResultsTable results={mockResults} onViewAttempt={handleView} />);

    const reviewButtons = screen.getAllByRole("button", { name: /review/i });
    expect(reviewButtons.length).toBeGreaterThan(0);

    fireEvent.click(reviewButtons[0]);
    expect(handleView).toHaveBeenCalledWith("att_1");
  });

  it("displays empty message when results list is empty", () => {
    render(<ExamResultsTable results={[]} emptyMessage="No students evaluated" />);

    expect(screen.getByText("No students evaluated")).toBeInTheDocument();
  });
});
