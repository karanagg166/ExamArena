import { create } from "zustand";
import { api } from "@/lib/axios";
import type { Question, QuestionCreate, QuestionUpsert } from "@/types";
import { detailFromError } from "@/lib/error";

interface QuestionState {
  questions: Question[];
  activeQuestion: Question | null;
  loading: boolean;
  error: string | null;

  setQuestions: (questions: Question[]) => void;
  setActiveQuestion: (question: Question | null) => void;
  fetchQuestionsByExamId: (examId: string) => Promise<void>;
  createQuestion: (
    payload: QuestionCreate & { examId: string }
  ) => Promise<{ success: boolean; data?: Question; error?: string }>;
  updateQuestion: (
    questionId: string,
    payload: Partial<QuestionUpsert>
  ) => Promise<{ success: boolean; data?: Question; error?: string }>;
  deleteQuestion: (
    questionId: string
  ) => Promise<{ success: boolean; error?: string }>;
  reset: () => void;
}

const initial = {
  questions: [],
  activeQuestion: null,
  loading: false,
  error: null,
};

export const useQuestionStore = create<QuestionState>((set) => ({
  ...initial,

  setQuestions: (questions) => set({ questions }),

  setActiveQuestion: (activeQuestion) => set({ activeQuestion }),

  fetchQuestionsByExamId: async (examId: string) => {
    set({ loading: true, error: null });
    try {
      const res = await api.get<{ questions?: Question[] }>(`/api/v1/exams/${examId}`);
      set({ questions: res.data.questions || [] });
    } catch (err) {
      set({ error: detailFromError(err, "Failed to load questions.") });
    } finally {
      set({ loading: false });
    }
  },

  createQuestion: async (payload) => {
    set({ loading: true, error: null });
    try {
      const res = await api.post<Question>("/api/v1/questions", payload);
      const newQuestion = res.data;
      set((state) => ({
        questions: [...state.questions, newQuestion],
        activeQuestion: newQuestion,
      }));
      return { success: true, data: newQuestion };
    } catch (err) {
      const msg = detailFromError(err, "Failed to create question.");
      set({ error: msg });
      return { success: false, error: msg };
    } finally {
      set({ loading: false });
    }
  },

  updateQuestion: async (questionId, payload) => {
    set({ loading: true, error: null });
    try {
      const res = await api.patch<Question>(`/api/v1/questions/${questionId}`, payload);
      const updated = res.data;
      set((state) => ({
        questions: state.questions.map((q) => (q.id === questionId ? updated : q)),
        activeQuestion:
          state.activeQuestion?.id === questionId ? updated : state.activeQuestion,
      }));
      return { success: true, data: updated };
    } catch (err) {
      const msg = detailFromError(err, "Failed to update question.");
      set({ error: msg });
      return { success: false, error: msg };
    } finally {
      set({ loading: false });
    }
  },

  deleteQuestion: async (questionId) => {
    set({ loading: true, error: null });
    try {
      await api.delete(`/api/v1/questions/${questionId}`);
      set((state) => ({
        questions: state.questions.filter((q) => q.id !== questionId),
        activeQuestion:
          state.activeQuestion?.id === questionId ? null : state.activeQuestion,
      }));
      return { success: true };
    } catch (err) {
      const msg = detailFromError(err, "Failed to delete question.");
      set({ error: msg });
      return { success: false, error: msg };
    } finally {
      set({ loading: false });
    }
  },

  reset: () => set(initial),
}));
