// src/stores/useSchoolStore.ts
import { create } from "zustand"
import { api } from "@/lib/axios"
import { School } from "@/types"

interface SchoolState {
    school: School | null
    loading: boolean
    error: string

    fetchSchool: () => Promise<void>
    reset: () => void
}

const initial = { school: null, loading: false, error: "" }

export const useSchoolStore = create<SchoolState>((set) => ({
    ...initial,

    fetchSchool: async () => {
        set({ loading: true, error: "" });
        console.log("Fetching school data...");
        try {
            const res = await api.get("/api/v1/schools/me");
            console.log("Fetched school data:", res.data);
            set({ school: res.data })
        } catch (error: unknown) {
            console.error("Error fetching school data:", error);
            set({ error: "Failed to load school" })
        } finally {
            set({ loading: false })
        }
    },

    reset: () => set(initial),
}))