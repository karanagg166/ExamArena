import { create } from "zustand";
import { User } from "@/types";
import { api } from "@/lib/axios";
import { useAttemptStore } from "./useAttemptStore";

interface AuthState {
  user: User | null;
  loading: boolean;
  initialized: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchMe: () => Promise<void>;
}
export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: false,
  initialized: false,
  error: null,
  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      await api.post("/api/v1/auth/login", { email, password });
      await useAuthStore.getState().fetchMe();
      set({ initialized: true });
    } catch (error: unknown) {
      console.error("Login failed:", error);
      set({ user: null, initialized: true });
      set({ error: "Invalid email or password" });
    } finally {
      set({ loading: false });
    }
  },
  logout: async () => {
    set({ loading: true, error: null });
    try {
      await api.post("/api/v1/auth/logout");
      set({ user: null, initialized: true });
      useAttemptStore.getState().clearAttempt();
    } catch (error: unknown) {
      console.error("Logout failed:", error);
      set({ error: "Failed to logout", initialized: true });
    } finally {
      set({ loading: false });
    }
  },
  fetchMe: async () => {
    set({ loading: true, error: null });
    try {
      const response = await api.get("/api/v1/auth/me");
      const fetchedUser = response.data;
      const currentAttemptUserId = useAttemptStore.getState().userId;
      if (currentAttemptUserId && fetchedUser?.id && currentAttemptUserId !== fetchedUser.id) {
        useAttemptStore.getState().clearAttempt();
      }
      set({ user: fetchedUser, initialized: true });
      console.log("Fetched user:", response.data);
    } catch (error: unknown) {
      console.error("Failed to fetch user:", error);
      set({ user: null, error: "Failed to fetch user", initialized: true });
    } finally {
      set({ loading: false });
    }
  },
}));
