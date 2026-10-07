import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { CourseMaterialsQA } from "@/components/course-materials/CourseMaterialsQA";
import * as apiModule from "@/lib/api/course-materials";
import type { GroundedAnswer } from "@/types/course-materials";

vi.mock("@/lib/api/course-materials", () => ({
  askCourseMaterials: vi.fn(),
}));

describe("CourseMaterialsQA Component", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders question input and ask button in idle state", () => {
    render(<CourseMaterialsQA defaultSubject="SCIENCE" />);

    expect(
      screen.getByText(/Ask about these materials/i),
    ).toBeDefined();
    const input = screen.getByLabelText(/Question about course materials/i);
    expect(input).toBeDefined();
    const askButton = screen.getByRole("button", { name: /^Ask$/i });
    expect(askButton).toBeDefined();
    expect(askButton.hasAttribute("disabled")).toBe(true);
  });

  it("shows loading state with 'Searching course materials...' text during submission", async () => {
    let resolvePromise: (value: GroundedAnswer) => void = () => {};
    const pendingPromise = new Promise<GroundedAnswer>((resolve) => {
      resolvePromise = resolve;
    });

    vi.mocked(apiModule.askCourseMaterials).mockReturnValue(pendingPromise);

    render(<CourseMaterialsQA defaultSubject="SCIENCE" />);

    const input = screen.getByLabelText(/Question about course materials/i);
    fireEvent.change(input, { target: { value: "Explain gravity" } });

    const askButton = screen.getByRole("button", { name: /^Ask$/i });
    expect(askButton.hasAttribute("disabled")).toBe(false);
    fireEvent.click(askButton);

    expect(screen.getByTestId("loading-state")).toBeDefined();
    expect(screen.getByText("Searching course materials...")).toBeDefined();

    // Resolve promise
    resolvePromise({
      answer: "Gravity is a fundamental force.",
      citations: [],
    });

    await waitFor(() => {
      expect(screen.queryByTestId("loading-state")).toBeNull();
    });
  });

  it("renders grounded answer and formatted citations on success", async () => {
    const mockSuccessAnswer: GroundedAnswer = {
      answer:
        "Total internal reflection occurs when the angle of incidence exceeds the critical angle [1].",
      citations: [
        {
          citationNumber: 1,
          title: "Class 10 Physics Notes",
          fileName: "physics_ch10.pdf",
          pageNumber: 12,
          textSnippet:
            "Light traveling from denser to rarer medium reflects completely back.",
          materialId: "mat_1",
        },
        {
          citationNumber: 2,
          title: "NCERT Physics",
          fileName: "ncert_physics.pdf",
          pageNumber: 45,
          textSnippet: "Critical angle condition for total reflection.",
          materialId: "mat_2",
        },
      ],
      retrievedChunkCount: 2,
      durationMs: 38.0,
    };

    vi.mocked(apiModule.askCourseMaterials).mockResolvedValue(mockSuccessAnswer);

    render(<CourseMaterialsQA defaultSubject="SCIENCE" classId="cls_101" />);

    const input = screen.getByLabelText(/Question about course materials/i);
    fireEvent.change(input, {
      target: { value: "Explain total internal reflection" },
    });

    fireEvent.click(screen.getByRole("button", { name: /^Ask$/i }));

    await waitFor(() => {
      expect(screen.getByTestId("answer-state")).toBeDefined();
    });

    // Check answer content
    expect(
      screen.getByText(
        /Total internal reflection occurs when the angle of incidence exceeds the critical angle/i,
      ),
    ).toBeDefined();

    // Check sources title
    expect(screen.getByText("Sources")).toBeDefined();

    // Check citation items
    expect(screen.getByTestId("citation-1")).toBeDefined();
    expect(screen.getByText(/Class 10 Physics Notes/i)).toBeDefined();
    expect(screen.getByText(/Page 12/i)).toBeDefined();
    expect(
      screen.getByText(
        /Light traveling from denser to rarer medium reflects completely back/i,
      ),
    ).toBeDefined();

    expect(screen.getByTestId("citation-2")).toBeDefined();
    expect(screen.getByText(/NCERT Physics/i)).toBeDefined();
    expect(screen.getByText(/Page 45/i)).toBeDefined();
  });

  it("renders no-evidence state when Search-Sphere finds insufficient information", async () => {
    const mockNoEvidence: GroundedAnswer = {
      answer:
        "I couldn't find relevant information in your documents to answer that question.",
      citations: [],
      retrievedChunkCount: 0,
      durationMs: 14.5,
    };

    vi.mocked(apiModule.askCourseMaterials).mockResolvedValue(mockNoEvidence);

    render(<CourseMaterialsQA defaultSubject="SCIENCE" />);

    const input = screen.getByLabelText(/Question about course materials/i);
    fireEvent.change(input, {
      target: { value: "What is quantum gravity equation?" },
    });

    fireEvent.click(screen.getByRole("button", { name: /^Ask$/i }));

    await waitFor(() => {
      expect(screen.getByTestId("no-evidence-state")).toBeDefined();
    });

    expect(screen.getByText(/Insufficient Evidence/i)).toBeDefined();
    expect(
      screen.getByText(/I couldn't find relevant information in your documents/i),
    ).toBeDefined();
    expect(screen.queryByTestId("citations-state")).toBeNull();
  });

  it("renders provider unavailable error state on 502/503 from backend", async () => {
    const error502 = {
      isAxiosError: true,
      response: {
        status: 502,
        data: { detail: "Search-Sphere service error" },
      },
    };

    vi.mocked(apiModule.askCourseMaterials).mockRejectedValue(error502);

    render(<CourseMaterialsQA defaultSubject="SCIENCE" />);

    const input = screen.getByLabelText(/Question about course materials/i);
    fireEvent.change(input, { target: { value: "Explain optics" } });

    fireEvent.click(screen.getByRole("button", { name: /^Ask$/i }));

    await waitFor(() => {
      expect(screen.getByTestId("unavailable-state")).toBeDefined();
    });

    expect(screen.getByText(/Service Unavailable/i)).toBeDefined();
    expect(
      screen.getByText(
        /Course material search service is temporarily unavailable/i,
      ),
    ).toBeDefined();
  });

  it("renders authorization error state on 403 Forbidden from backend", async () => {
    const error403 = {
      isAxiosError: true,
      response: {
        status: 403,
        data: {
          detail:
            "Students can only search course materials for their enrolled class.",
        },
      },
    };

    vi.mocked(apiModule.askCourseMaterials).mockRejectedValue(error403);

    render(<CourseMaterialsQA defaultSubject="SCIENCE" classId="cls_other" />);

    const input = screen.getByLabelText(/Question about course materials/i);
    fireEvent.change(input, { target: { value: "Explain photosynthesis" } });

    fireEvent.click(screen.getByRole("button", { name: /^Ask$/i }));

    await waitFor(() => {
      expect(screen.getByTestId("unauthorized-state")).toBeDefined();
    });

    expect(screen.getByText(/Access Restricted/i)).toBeDefined();
    expect(
      screen.getByText(
        /Students can only search course materials for their enrolled class/i,
      ),
    ).toBeDefined();
  });
});
