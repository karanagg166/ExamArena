import { create } from "zustand";

import { api } from "@/lib/axios";
import { getErrorMessage } from "@/lib/error";
import type { ClassJoinRequest, JoinRequestStatus } from "@/types";

type Result = { success: boolean; error?: string };

type JoinRequestState = {
  myRequests: ClassJoinRequest[];
  classRequests: ClassJoinRequest[];
  schoolRequests: ClassJoinRequest[];
  loading: boolean;
  error: string;
  joinByCode: (joinCode: string) => Promise<Result>;
  fetchMyRequests: () => Promise<void>;
  fetchClassRequests: (classId: string, status?: JoinRequestStatus) => Promise<void>;
  fetchSchoolRequests: (schoolId: string, status?: JoinRequestStatus) => Promise<void>;
  decideRequest: (
    requestId: string,
    status: "APPROVED" | "REJECTED",
    options?: { rollNo?: string; autoRollNo?: boolean }
  ) => Promise<Result>;
  reset: () => void;
};

const initial = {
  myRequests: [],
  classRequests: [],
  schoolRequests: [],
  loading: false,
  error: "",
};

import { getErrorMessage } from "@/lib/error";

const detailFromError = (error: unknown, fallback: string) => {
  const msg = getErrorMessage(error);
  return msg && msg !== "An unexpected error occurred." ? msg : fallback;
};

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

  fetchSchoolRequests: async (schoolId, status) => {
    set({ loading: true, error: "" });
    try {
      const response = await api.get(`/api/v1/join-requests/school/${schoolId}`, {
        params: status ? { status } : undefined,
      });
      set({ schoolRequests: response.data });
    } catch (error) {
      set({ error: detailFromError(error, "Unable to load school join requests.") });
    } finally {
      set({ loading: false });
    }
  },

  decideRequest: async (requestId, status, options) => {
    set({ loading: true, error: "" });
    try {
      const payload = {
        status,
        rollNo: options?.rollNo,
        autoRollNo: options?.autoRollNo ?? true,
      };
      const response = await api.patch(`/api/v1/join-requests/${requestId}`, payload);
      set((state) => ({
        classRequests: state.classRequests.filter((request) => request.id !== response.data.id),
        schoolRequests: state.schoolRequests.filter((request) => request.id !== response.data.id),
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

