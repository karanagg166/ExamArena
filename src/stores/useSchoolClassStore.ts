// src/stores/useSchoolClassStore.ts
import { create } from "zustand";
import { api } from "@/lib/axios";
import { SchoolClass, CreateClassRequest } from "@/types";

interface SchoolClassState {
  classes: SchoolClass[];
  loading: boolean;
  error: string;

  fetchClassesBySchool: (schoolId: string) => Promise<void>;
  fetchClass: (classId: string) => Promise<void>;
  createClass: (data: CreateClassRequest) => Promise<boolean>;
  clearClasses: () => void; // ✅ added
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
      set((state) => ({ classes: [...state.classes, res.data] }));
      return true;
    } catch (error: unknown) {
      set({ error: "Failed to create class" });
      console.error("Error creating class:", error);
      return false;
    } finally {
      set({ loading: false });
    }
  },

  clearClasses: () => set({ classes: [] }), // ✅ only clears classes
  reset: () => set(initial), // resets everything
}));
