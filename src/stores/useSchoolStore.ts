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
        set({ loading: true, error: "" })
        try {
            const res = await api.get("/api/v1/schools/me")
            set({ school: res.data })
        } catch {
            set({ error: "Failed to load school" })
        } finally {
            set({ loading: false })
        }
    },

    reset: () => set(initial),
}))