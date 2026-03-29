import { create } from "zustand";
import { api } from "@/lib/axios";
import { Student } from "@/types";

interface StudentState {
  student: Student | null;
  loading: boolean;
  error: string;

  fetchStudentByUserId: (userId: string) => Promise<void>;
  fetchStudentById: (studentId: string) => Promise<void>;
  fecthStudentsByClassId: (classId: string) => Promise<void>;
  updateStudent: (data: Student) => Promise<boolean>;

  reset: () => void;
}

const intial = { student: null, loading: false, error: "" };

export const useStudentStore = create<StudentState>((set) => ({
  ...intial,

  fetchStudentByUserId: async (userId) => {
    set({ loading: true, error: "" });
    try {
      const res = await api.get(`/api/v1/students/user/${userId}`);
      set({ student: res.data });
    } catch {
      set({ error: "Failed to load student" });
    } finally {
      set({ loading: false });
    }
  },

  fetchStudentById: async (studentId) => {
    set({ loading: true, error: "" });
    try {
      const res = await api.get(`/api/v1/students/${studentId}`);
      set({ student: res.data });
    } catch {
      set({ error: "Failed to load student" });
    } finally {
      set({ loading: false });
    }
  },

  fecthStudentsByClassId: async (classId) => {
    set({ loading: true, error: "" });
    try {
      const res = await api.get(`/api/v1/students/class/${classId}`);
      set({ student: res.data });
    } catch {
      set({ error: "Failed to load students" });
    } finally {
      set({ loading: false });
    }
  },

  updateStudent: async (data) => {
    set({ loading: true, error: "" });
    try {
      await api.put("/api/v1/students/", data);
      return true;
    } catch {
      set({ error: "Failed to update student" });
      return false;
    } finally {
      set({ loading: false });
    }
  },

  reset: () => set(intial),
}));
