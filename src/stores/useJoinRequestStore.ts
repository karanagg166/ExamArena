import axios from "axios";
import { create } from "zustand";

import { api } from "@/lib/axios";
import type { ClassJoinRequest, JoinRequestStatus } from "@/types";

type Result = { success: boolean; error?: string };

type JoinRequestState = {
  myRequests: ClassJoinRequest[];
  classRequests: ClassJoinRequest[];
  loading: boolean;
  error: string;
  joinByCode: (joinCode: string) => Promise<Result>;
  fetchMyRequests: () => Promise<void>;
  fetchClassRequests: (classId: string, status?: JoinRequestStatus) => Promise<void>;
  decideRequest: (requestId: string, status: "APPROVED" | "REJECTED") => Promise<Result>;
  reset: () => void;
};

const initial = { myRequests: [], classRequests: [], loading: false, error: "" };

const detailFromError = (error: unknown, fallback: string) =>
  axios.isAxiosError(error) && typeof error.response?.data?.detail === "string"
    ? error.response.data.detail
    : fallback;

export const useJoinRequestStore = create<JoinRequestState>((set) => ({
  ...initial,

  joinByCode: async (joinCode) => {
    set({ loading: true, error: "" });
    try {
      const response = await api.post("/api/v1/join-requests/join-by-code", { joinCode });
      set((state) => ({
        myRequests: [
          response.data,
          ...state.myRequests.filter((request) => request.id !== response.data.id),
        ],
      }));
      return { success: true };
    } catch (error) {
      const message = detailFromError(error, "Unable to submit the join request.");
      set({ error: message });
      return { success: false, error: message };
    } finally {
      set({ loading: false });
    }
  },

  fetchMyRequests: async () => {
    set({ loading: true, error: "" });
    try {
      const response = await api.get("/api/v1/join-requests/me");
      set({ myRequests: response.data });
    } catch (error) {
      set({ error: detailFromError(error, "Unable to load enrollment status.") });
    } finally {
      set({ loading: false });
    }
  },

  fetchClassRequests: async (classId, status = "PENDING") => {
    set({ loading: true, error: "" });
    try {
      const response = await api.get(`/api/v1/join-requests/class/${classId}`, {
        params: { status },
      });
      set({ classRequests: response.data });
    } catch (error) {
      set({ error: detailFromError(error, "Unable to load join requests.") });
    } finally {
      set({ loading: false });
    }
  },

  decideRequest: async (requestId, status) => {
    set({ loading: true, error: "" });
    try {
      const response = await api.patch(`/api/v1/join-requests/${requestId}`, { status });
      set((state) => ({
        classRequests: state.classRequests.filter((request) => request.id !== response.data.id),
      }));
      return { success: true };
    } catch (error) {
      const message = detailFromError(error, "Unable to update the request.");
      set({ error: message });
      return { success: false, error: message };
    } finally {
      set({ loading: false });
    }
  },

  reset: () => set(initial),
}));
