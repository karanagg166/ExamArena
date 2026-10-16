import { create } from "zustand";
import { api } from "@/lib/axios";
import type { Teacher } from "@/types";
import { detailFromError } from "@/lib/error";

interface TeacherState {
  teacher: Teacher | null;
  teachers: Teacher[];
  loading: boolean;
  error: string;

  fetchTeacherMe: () => Promise<void>;
  fetchTeacherById: (teacherId: string) => Promise<void>;
  fetchTeachersBySchool: (schoolId: string) => Promise<void>;
  updateTeacherMe: (data: Partial<Teacher>) => Promise<boolean>;

  reset: () => void;
}

const initial = {
  teacher: null,
  teachers: [],
  loading: false,
  error: "",
};

export const useTeacherStore = create<TeacherState>((set) => ({
  ...initial,

  fetchTeacherMe: async () => {
    set({ loading: true, error: "" });
    try {
      const res = await api.get<Teacher>("/api/v1/teachers/me");
      set({ teacher: res.data });
    } catch (error) {
      set({ error: detailFromError(error, "Failed to load teacher profile.") });
    } finally {
      set({ loading: false });
    }
  },

  fetchTeacherById: async (teacherId: string) => {
    set({ loading: true, error: "" });
    try {
      const res = await api.get<Teacher>(`/api/v1/teachers/${teacherId}`);
      set({ teacher: res.data });
    } catch (error) {
      set({ error: detailFromError(error, "Failed to load teacher details.") });
    } finally {
      set({ loading: false });
    }
  },

  fetchTeachersBySchool: async (schoolId: string) => {
    set({ loading: true, error: "" });
    try {
      const res = await api.get<Teacher[]>(`/api/v1/teachers?schoolId=${schoolId}`);
      set({ teachers: res.data || [] });
    } catch (error) {
      set({ error: detailFromError(error, "Failed to load school faculty roster.") });
    } finally {
      set({ loading: false });
    }
  },

  updateTeacherMe: async (data: Partial<Teacher>) => {
    set({ loading: true, error: "" });
    try {
      const res = await api.put<Teacher>("/api/v1/teachers/me", data);
      set({ teacher: res.data });
      return true;
    } catch (error) {
      set({ error: detailFromError(error, "Failed to update teacher profile.") });
      return false;
    } finally {
      set({ loading: false });
    }
  },

  reset: () => set(initial),
}));
