// src/stores/useSchoolClassStore.ts
import { create } from "zustand";
import { api } from "@/lib/axios";
import { SchoolClass, CreateClassRequest } from "@/types";

interface SchoolClassState {
  classes: SchoolClass[];
  loading: boolean;
  error: string;

  fetchClasses: (schoolId: string) => Promise<void>;
  createClass: (data: CreateClassRequest) => Promise<boolean>; // returns true on success
  reset: () => void;
}

const initial = { classes: [], loading: false, error: "" };

export const useSchoolClassStore = create<SchoolClassState>((set) => ({
  ...initial,

  fetchClasses: async (schoolId) => {
    set({ loading: true, error: "" });
    try {
      const res = await api.get(`/api/v1/classes/?schoolId=${schoolId}`);
      set({ classes: res.data });
    } catch {
      set({ error: "Failed to load classes" });
    } finally {
      set({ loading: false });
    }
  },

  createClass: async (data) => {
    set({ loading: true, error: "" });
    console.log("Creating class with data:", data);
    try {
      const res = await api.post("/api/v1/classes/", data);
      console.log("Create class response:", res);
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

  reset: () => set(initial),
}));
