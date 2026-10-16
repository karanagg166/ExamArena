import { describe, it, expect, beforeEach, vi } from "vitest";
import { useQuestionStore } from "@/stores/useQuestionStore";
import { api } from "@/lib/axios";
import type { Question } from "@/types";

vi.mock("@/lib/axios", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockQuestion: Question = {
  id: "q_1",
  questionNumber: 1,
  text: "What is time complexity of binary search?",
  section: "Section A",
  marks: 2,
  negativeMarks: 0.5,
  questionType: "MULTIPLE_CHOICE",
  examId: "ex_1",
  createdAt: "2026-01-01T00:00:00Z",
  updatedAt: "2026-01-01T00:00:00Z",
  options: [
    { id: "opt_1", optionNumber: 1, questionId: "q_1", text: "O(log n)", isCorrect: true },
    { id: "opt_2", optionNumber: 2, questionId: "q_1", text: "O(n)", isCorrect: false },
  ],
};

describe("Unit: useQuestionStore", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useQuestionStore.getState().reset();
  });

  it("fetchQuestionsByExamId loads questions from exam", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: { questions: [mockQuestion] },
    });

    await useQuestionStore.getState().fetchQuestionsByExamId("ex_1");

    expect(api.get).toHaveBeenCalledWith("/api/v1/exams/ex_1");
    expect(useQuestionStore.getState().questions).toEqual([mockQuestion]);
  });

  it("createQuestion appends question on success", async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: mockQuestion });

    const res = await useQuestionStore.getState().createQuestion({
      examId: "ex_1",
      questionNumber: 1,
      text: "What is time complexity of binary search?",
      section: "Section A",
      marks: 2,
      questionType: "MULTIPLE_CHOICE",
    });

    expect(res.success).toBe(true);
    expect(res.data).toEqual(mockQuestion);
    expect(useQuestionStore.getState().questions).toHaveLength(1);
    expect(useQuestionStore.getState().activeQuestion).toEqual(mockQuestion);
  });

  it("updateQuestion modifies existing question in state", async () => {
    useQuestionStore.setState({
      questions: [mockQuestion],
      activeQuestion: mockQuestion,
    });

    const updated = { ...mockQuestion, marks: 4 };
    vi.mocked(api.patch).mockResolvedValueOnce({ data: updated });

    const res = await useQuestionStore
      .getState()
      .updateQuestion("q_1", { marks: 4 });

    expect(res.success).toBe(true);
    expect(useQuestionStore.getState().questions[0].marks).toBe(4);
    expect(useQuestionStore.getState().activeQuestion?.marks).toBe(4);
  });

  it("deleteQuestion removes question from state", async () => {
    useQuestionStore.setState({
      questions: [mockQuestion],
      activeQuestion: mockQuestion,
    });

    vi.mocked(api.delete).mockResolvedValueOnce({ data: {} });

    const res = await useQuestionStore.getState().deleteQuestion("q_1");

    expect(res.success).toBe(true);
    expect(useQuestionStore.getState().questions).toHaveLength(0);
    expect(useQuestionStore.getState().activeQuestion).toBeNull();
  });
});
