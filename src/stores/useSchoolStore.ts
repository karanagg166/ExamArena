// src/stores/useSchoolStore.ts
import { create } from "zustand";
import { api } from "@/lib/axios";
import { School } from "@/types";

interface SchoolState {
  school: School | null;
  loading: boolean;
  hasFetched: boolean;
  error: string;

  fetchSchool: () => Promise<void>;
  fetchSchoolById: (schoolId: string) => Promise<void>;
  reset: () => void;
}

const initial = { school: null, loading: false, hasFetched: false, error: "" };

export const useSchoolStore = create<SchoolState>((set) => ({
  ...initial,

  fetchSchool: async () => {
    set({ loading: true, error: "" });
    try {
      const res = await api.get("/api/v1/schools/me");
      set({ school: res.data, hasFetched: true, error: "" });
    } catch (error: unknown) {
      const status = (error as { response?: { status?: number } })?.response?.status;
      if (status === 404) {
        // User has not created or joined a school yet — normal valid state
        set({ school: null, hasFetched: true, error: "" });
      } else {
        set({ error: "Failed to load school", hasFetched: true });
      }
    } finally {
      set({ loading: false });
    }
  },
  fetchSchoolById: async (schoolId: string) => {
    set({ loading: true, error: "" });
    try {
      const res = await api.get(`/api/v1/schools/${schoolId}`);
      set({ school: res.data, hasFetched: true, error: "" });
    } catch (error: unknown) {
      const status = (error as { response?: { status?: number } })?.response?.status;
      if (status === 404) {
        set({ school: null, hasFetched: true, error: "" });
      } else {
        set({ error: "Failed to load school", hasFetched: true });
      }
    } finally {
      set({ loading: false });
    }
  },

  reset: () => set(initial),
}));

