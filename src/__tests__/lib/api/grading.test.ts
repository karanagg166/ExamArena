import { beforeEach, expect, it, vi } from "vitest";
import { api } from "@/lib/axios";
import { gradingApi } from "@/lib/api/grading";
vi.mock("@/lib/axios", () => ({
  api: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
}));
beforeEach(() => vi.resetAllMocks());
it("uses the authenticated client and actual grading routes without recasing response fields", async () => {
  const detail = {
    id: "a1",
    referenceAnswer: "Teacher context",
    aiProposal: null,
    finalGrade: null,
  };
  vi.mocked(api.get).mockResolvedValue({ data: detail });
  expect(await gradingApi.getAnswer("a1")).toBe(detail);
  expect(api.get).toHaveBeenCalledWith("/api/v1/student-answers/a1");
  const proposal = {
    suggestedMarks: 4.5,
    rubricBreakdown: [],
    confidence: "HIGH",
  };
  vi.mocked(api.post).mockResolvedValue({ data: proposal });
  expect(await gradingApi.generateAiGrade("a1")).toBe(proposal);
  expect(api.post).toHaveBeenCalledWith("/api/v1/student-answers/a1/ai-grade");
  await gradingApi.acceptAiGrade("a1");
  expect(api.post).toHaveBeenCalledWith(
    "/api/v1/student-answers/a1/grade/accept-ai",
  );
  const payload = { marks: 4.25, feedback: "Teacher feedback" };
  vi.mocked(api.patch).mockResolvedValue({ data: { marksAwarded: 4.25 } });
  await gradingApi.updateManualGrade("a1", payload);
  expect(api.patch).toHaveBeenCalledWith(
    "/api/v1/student-answers/a1/grade",
    payload,
  );
  await gradingApi.rejectAiGrade("a1");
  expect(api.post).toHaveBeenCalledWith(
    "/api/v1/student-answers/a1/grade/reject-ai",
  );
  await gradingApi.getAttempt("at1");
  expect(api.get).toHaveBeenCalledWith("/api/v1/attempts/at1");
});
