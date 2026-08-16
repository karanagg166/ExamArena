import { create } from "zustand";
import axios from "axios";
import { api } from "@/lib/axios";
import { SchoolClass, CreateClassRequest } from "@/types";

interface SchoolClassState {
  classes: SchoolClass[];
  loading: boolean;
  error: string;

  fetchClassesBySchool: (schoolId: string) => Promise<void>;
  fetchClass: (classId: string) => Promise<void>;
  createClass: (
    data: CreateClassRequest,
  ) => Promise<{ success: boolean; data?: SchoolClass; error?: string }>;
  deleteClass: (classId: string) => Promise<boolean>;
  clearClasses: () => void;
  reset: () => void;
}

const initial = { classes: [], loading: false, error: "" };

export const useSchoolClassStore = create<SchoolClassState>((set) => ({
  ...initial,

  fetchClassesBySchool: async (schoolId) => {
    set({ loading: true, error: "" });
    try {
      const res = await api.get(`/api/v1/classes/school/${schoolId}`);
      set({ classes: res.data });
    } catch {
      set({ error: "Failed to load classes" });
    } finally {
      set({ loading: false });
    }
  },

  fetchClass: async (classId) => {
    set({ loading: true, error: "" });
    try {
      const res = await api.get(`/api/v1/classes/${classId}`);
      set((state) => ({
        classes: state.classes.some((c) => c.id === classId)
          ? state.classes.map((c) => (c.id === classId ? res.data : c))
          : [...state.classes, res.data],
      }));
    } catch {
      set({ error: "Failed to load class" });
    } finally {
      set({ loading: false });
    }
  },

  createClass: async (data) => {
    set({ loading: true, error: "" });
    try {
      const res = await api.post("/api/v1/classes/", {
        name: data.name,
        year: data.year,
        section: data.section,
      });
      set((state) => ({ classes: [...state.classes, res.data], error: "" }));
      return { success: true, data: res.data };
    } catch (err: unknown) {
      let errorMsg = `Class '${data.name}' already exists.`;
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        if (typeof detail === "string") {
          if (
            detail.toLowerCase().includes("already exists") ||
            detail.toLowerCase().includes("duplicate") ||
            detail.toLowerCase().includes("unique constraint")
          ) {
            errorMsg = `Class '${data.name}' already exists of same name.`;
          } else {
            errorMsg = detail;
          }
        } else if (
          err.response?.status === 400 ||
          err.response?.status === 409
        ) {
          errorMsg = `Class '${data.name}' already exists of same name.`;
        }
      }
      set({ error: errorMsg });
      console.error("Error creating class:", err);
      return { success: false, error: errorMsg };
    } finally {
      set({ loading: false });
    }
  },

  deleteClass: async (classId: string) => {
    set({ loading: true, error: "" });
    try {
      await api.delete(`/api/v1/classes/${classId}`);
      set((state) => ({
        classes: state.classes.filter((c) => c.id !== classId),
      }));
      return true;
    } catch (err: unknown) {
      console.error("Error deleting class:", err);
      set({ error: "Failed to delete class" });
      return false;
    } finally {
      set({ loading: false });
    }
  },

  clearClasses: () => set({ classes: [] }), // ✅ only clears classes
  reset: () => set(initial), // resets everything
}));
