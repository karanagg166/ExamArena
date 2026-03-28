import { create } from "zustand";
import { User } from "@/types";
import { api } from "@/lib/axios";
interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchMe: () => Promise<void>;
}
export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: false,
  error: null,
  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      await api.post("/api/v1/auth/login", { email, password });
      await useAuthStore.getState().fetchMe();
      console.log("Login attempted with:", { email, password });
    } catch (error: unknown) {
      console.error("Login failed:", error);
      set({ user: null });

      set({ error: "Invalid email or password" });
    } finally {
      set({ loading: false });
    }
  },
  logout: async () => {
    set({ loading: true, error: null });
    try {
      await api.post("/api/v1/auth/logout");
      set({ user: null });
    } catch (error: unknown) {
      console.error("Logout failed:", error);
      set({ error: "Failed to logout" });
    } finally {
      set({ loading: false });
    }
  },
  fetchMe: async () => {
    set({ loading: true, error: null });
    try {
      const response = await api.get("/api/v1/auth/me");
      set({ user: response.data });
      console.log("Fetched user:", response.data);
    } catch (error: unknown) {
      console.error("Failed to fetch user:", error);
      set({ error: "Failed to fetch user" });
    } finally {
      set({ loading: false });
    }
  },
}));
