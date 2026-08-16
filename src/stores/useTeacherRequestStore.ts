import axios from "axios";
import { create } from "zustand";

import { api } from "@/lib/axios";
import type {
  TeacherAssignClassesPayload,
  TeacherClassJoinRequest,
  TeacherSchoolJoinRequest,
} from "@/types";

type Result = { success: boolean; message?: string; error?: string };

type TeacherRequestState = {
  mySchoolRequests: TeacherSchoolJoinRequest[];
  myClassRequests: TeacherClassJoinRequest[];
  schoolTeacherClassRequests: TeacherClassJoinRequest[];
  schoolTeacherSchoolRequests: TeacherSchoolJoinRequest[];
  loading: boolean;
  error: string;

  fetchMySchoolRequests: () => Promise<void>;
  fetchMyClassRequests: () => Promise<void>;
  requestToJoinSchool: (schoolId: string) => Promise<Result>;
  requestToTeachClass: (classId: string, subject?: string) => Promise<Result>;

  fetchSchoolTeacherClassRequests: (schoolId: string, status?: string) => Promise<void>;
  fetchSchoolTeacherSchoolRequests: (schoolId: string, status?: string) => Promise<void>;

  decideTeacherSchoolRequest: (
    requestId: string,
    status: "APPROVED" | "REJECTED"
  ) => Promise<Result>;
  decideTeacherClassRequest: (
    requestId: string,
    status: "APPROVED" | "REJECTED"
  ) => Promise<Result>;

  assignClassesToTeacher: (payload: TeacherAssignClassesPayload) => Promise<Result>;
  reset: () => void;
};

const initial = {
  mySchoolRequests: [],
  myClassRequests: [],
  schoolTeacherClassRequests: [],
  schoolTeacherSchoolRequests: [],
  loading: false,
  error: "",
};

const detailFromError = (error: unknown, fallback: string) =>
  axios.isAxiosError(error) && typeof error.response?.data?.detail === "string"
    ? error.response.data.detail
    : fallback;

export const useTeacherRequestStore = create<TeacherRequestState>((set) => ({
  ...initial,

  fetchMySchoolRequests: async () => {
    set({ loading: true, error: "" });
    try {
      const { data } = await api.get<TeacherSchoolJoinRequest[]>(
        "/api/v1/teacher-requests/school/me"
      );
      set({ mySchoolRequests: data });
    } catch (error) {
      set({ error: detailFromError(error, "Unable to load school join requests.") });
    } finally {
      set({ loading: false });
    }
  },

  fetchMyClassRequests: async () => {
    set({ loading: true, error: "" });
    try {
      const { data } = await api.get<TeacherClassJoinRequest[]>(
        "/api/v1/teacher-requests/me"
      );
      set({ myClassRequests: data });
    } catch (error) {
      set({ error: detailFromError(error, "Unable to load class requests.") });
    } finally {
      set({ loading: false });
    }
  },

  requestToJoinSchool: async (schoolId: string) => {
    set({ loading: true, error: "" });
    try {
      const { data } = await api.post<TeacherSchoolJoinRequest>(
        "/api/v1/teacher-requests/school",
        { schoolId }
      );
      set((state) => ({
        mySchoolRequests: [
          data,
          ...state.mySchoolRequests.filter((r) => r.id !== data.id),
        ],
      }));
      return { success: true, message: "Join request submitted to principal." };
    } catch (error) {
      const msg = detailFromError(error, "Unable to submit join request.");
      set({ error: msg });
      return { success: false, error: msg };
    } finally {
      set({ loading: false });
    }
  },

  requestToTeachClass: async (classId: string, subject?: string) => {
    set({ loading: true, error: "" });
    try {
      const { data } = await api.post<TeacherClassJoinRequest>(
        "/api/v1/teacher-requests",
        { classId, subject }
      );
      set((state) => ({
        myClassRequests: [
          data,
          ...state.myClassRequests.filter((r) => r.id !== data.id),
        ],
      }));
      return { success: true, message: "Class request submitted." };
    } catch (error) {
      const msg = detailFromError(error, "Unable to submit class request.");
      set({ error: msg });
      return { success: false, error: msg };
    } finally {
      set({ loading: false });
    }
  },

  fetchSchoolTeacherClassRequests: async (schoolId: string, status?: string) => {
    set({ loading: true, error: "" });
    try {
      const { data } = await api.get<TeacherClassJoinRequest[]>(
        `/api/v1/teacher-requests/school/${schoolId}`,
        { params: status ? { status_filter: status } : undefined }
      );
      set({ schoolTeacherClassRequests: data });
    } catch (error) {
      set({ error: detailFromError(error, "Unable to load teacher class requests.") });
    } finally {
      set({ loading: false });
    }
  },

  fetchSchoolTeacherSchoolRequests: async (schoolId: string, status?: string) => {
    set({ loading: true, error: "" });
    try {
      const { data } = await api.get<TeacherSchoolJoinRequest[]>(
        `/api/v1/teacher-requests/school-requests/${schoolId}`,
        { params: status ? { status_filter: status } : undefined }
      );
      set({ schoolTeacherSchoolRequests: data });
    } catch (error) {
      set({ error: detailFromError(error, "Unable to load teacher school requests.") });
    } finally {
      set({ loading: false });
    }
  },

  decideTeacherSchoolRequest: async (requestId: string, status: "APPROVED" | "REJECTED") => {
    set({ loading: true, error: "" });
    try {
      const { data } = await api.patch<TeacherSchoolJoinRequest>(
        `/api/v1/teacher-requests/school-requests/${requestId}`,
        { status }
      );
      set((state) => ({
        schoolTeacherSchoolRequests: state.schoolTeacherSchoolRequests.map((r) =>
          r.id === requestId ? data : r
        ),
      }));
      return { success: true, message: `Request marked as ${status}` };
    } catch (error) {
      const msg = detailFromError(error, "Unable to update school request.");
      set({ error: msg });
      return { success: false, error: msg };
    } finally {
      set({ loading: false });
    }
  },

  decideTeacherClassRequest: async (requestId: string, status: "APPROVED" | "REJECTED") => {
    set({ loading: true, error: "" });
    try {
      const { data } = await api.patch<TeacherClassJoinRequest>(
        `/api/v1/teacher-requests/${requestId}`,
        { status }
      );
      set((state) => ({
        schoolTeacherClassRequests: state.schoolTeacherClassRequests.map((r) =>
          r.id === requestId ? data : r
        ),
      }));
      return { success: true, message: `Request marked as ${status}` };
    } catch (error) {
      const msg = detailFromError(error, "Unable to update class request.");
      set({ error: msg });
      return { success: false, error: msg };
    } finally {
      set({ loading: false });
    }
  },

  assignClassesToTeacher: async (payload: TeacherAssignClassesPayload) => {
    set({ loading: true, error: "" });
    try {
      const { data } = await api.post<{ message: string; assignedCount: number }>(
        "/api/v1/teacher-requests/assign-classes",
        payload
      );
      return { success: true, message: data.message };
    } catch (error) {
      const msg = detailFromError(error, "Failed to assign classes to teacher.");
      set({ error: msg });
      return { success: false, error: msg };
    } finally {
      set({ loading: false });
    }
  },

  reset: () => set(initial),
}));
