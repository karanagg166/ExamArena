import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/axios";
import { askCourseMaterials, courseMaterialsApi } from "@/lib/api/course-materials";
import type { GroundedAnswer } from "@/types/course-materials";

vi.mock("@/lib/axios", () => ({
  api: {
    post: vi.fn(),
  },
}));

beforeEach(() => {
  vi.resetAllMocks();
});

describe("courseMaterialsApi", () => {
  it("calls /api/v1/course-materials/answer with expected payload and returns data", async () => {
    const mockResponse: GroundedAnswer = {
      answer: "Total internal reflection occurs when angle of incidence exceeds critical angle. [1]",
      citations: [
        {
          citationNumber: 1,
          title: "Class 10 Physics Notes",
          fileName: "physics_ch10.pdf",
          pageNumber: 12,
          textSnippet: "When light travels from denser to rarer medium...",
          materialId: "mat_1",
          documentType: "TEXTBOOK",
        },
      ],
      retrievedChunkCount: 1,
      warnings: [],
      durationMs: 45.2,
    };

    vi.mocked(api.post).mockResolvedValue({ data: mockResponse });

    const requestPayload = {
      query: "Explain total internal reflection",
      subject: "SCIENCE",
      classId: "cls_10a",
    };

    const res = await askCourseMaterials(requestPayload);

    expect(api.post).toHaveBeenCalledWith(
      "/api/v1/course-materials/answer",
      requestPayload,
    );
    expect(res).toEqual(mockResponse);
    expect(res.answer).toContain("Total internal reflection");
    expect(res.citations).toHaveLength(1);
    expect(res.citations[0].citationNumber).toBe(1);

    const resFromApi = await courseMaterialsApi.ask(requestPayload);
    expect(resFromApi).toEqual(mockResponse);
  });
});
