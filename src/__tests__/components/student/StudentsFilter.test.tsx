import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import StudentsPage from "@/app/(protected)/(staff-only)/students/page";

vi.mock("@/lib/axios", () => ({
  api: {
    get: vi.fn().mockResolvedValue({ data: [] }),
  },
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

describe("StudentsPage Filter UI", () => {
  it("renders personal and class filters and does not render school filters", () => {
    render(<StudentsPage />);
    expect(screen.getByLabelText(/^Name$/i)).toBeDefined();
    expect(screen.getByLabelText(/^Email$/i)).toBeDefined();
    expect(screen.getByLabelText(/^Roll Number$/i)).toBeDefined();
    expect(screen.getByLabelText(/^Class Year$/i)).toBeDefined();
    expect(screen.getByLabelText(/^Section$/i)).toBeDefined();
    expect(screen.queryByLabelText(/School Name/i)).toBeNull();
    expect(screen.queryByLabelText(/School Code/i)).toBeNull();
  });
});
