import { create } from "zustand";
import { api } from "@/lib/axios";
import type { Exam, ExamCreate, ExamUpdate } from "@/types";
import axios from "axios";

interface ExamState {
  exams: Exam[];
  currentExam: Exam | null;
  loading: boolean;
  error: string | null;

  fetchExams: () => Promise<void>;
  fetchExamById: (examId: string) => Promise<void>;
  createExam: (data: ExamCreate) => Promise<Exam>;
  updateExam: (examId: string, data: ExamUpdate) => Promise<Exam>;
  reset: () => void;
  setError: (error: string | null) => void;
}

const initial = {
  exams: [],
  currentExam: null,
  loading: false,
  error: null,
};

const getErrorMessage = (error: unknown, fallback: string): string => {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail ?? fallback;
  }
  return fallback;
};

export const useExamStore = create<ExamState>((set) => ({
  ...initial,

  fetchExams: async () => {
    set({ loading: true, error: null });
    try {
      const res = await api.get("/api/v1/exams/");
      set({ exams: res.data });
    } catch (error: unknown) {
      console.error("Error fetching exams:", error);
      set({ error: getErrorMessage(error, "Failed to load exams.") });
    } finally {
      set({ loading: false });
    }
  },

  fetchExamById: async (examId: string) => {
    set({ loading: true, error: null });
    try {
      const res = await api.get(`/api/v1/exams/${examId}`);
      set({ currentExam: res.data });
    } catch (error: unknown) {
      console.error("Error fetching exam:", error);
      set({ error: getErrorMessage(error, "Failed to load exam details.") });
    } finally {
      set({ loading: false });
    }
  },

  createExam: async (data: ExamCreate) => {
    set({ loading: true, error: null });
    try {
      const res = await api.post("/api/v1/exams/", data);
      set((state) => ({
        exams: [...state.exams, res.data],
        currentExam: res.data,
      }));
      return res.data;
    } catch (error: unknown) {
      console.error("Error creating exam:", error);
      const msg = getErrorMessage(error, "Failed to create exam.");
      set({ error: msg });
      throw new Error(msg);
    } finally {
      set({ loading: false });
    }
  },

  updateExam: async (examId: string, data: ExamUpdate) => {
    set({ loading: true, error: null });
    try {
      const res = await api.patch(`/api/v1/exams/${examId}`, data);
      set((state) => ({
        exams: state.exams.map((e) => (e.id === examId ? res.data : e)),
        currentExam:
          state.currentExam?.id === examId ? res.data : state.currentExam,
      }));
      return res.data;
    } catch (error: unknown) {
      console.error("Error updating exam:", error);
      const msg = getErrorMessage(error, "Failed to update exam.");
      set({ error: msg });
      throw new Error(msg);
    } finally {
      set({ loading: false });
    }
  },

  reset: () => set(initial),
  setError: (error: string | null) => set({ error }),
}));