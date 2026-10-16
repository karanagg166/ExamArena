import { describe, it, expect, beforeEach, vi } from "vitest";
import { useTeacherStore } from "@/stores/useTeacherStore";
import { api } from "@/lib/axios";
import type { Teacher } from "@/types";

vi.mock("@/lib/axios", () => ({
  api: {
    get: vi.fn(),
    put: vi.fn(),
  },
}));

const mockTeacher: Teacher = {
  id: "tch_1",
  userId: "usr_1",
  name: "Dr. Sharma",
  email: "sharma@school.edu",
  phoneNo: "+919876543210",
  experience: 8,
  qualifications: ["Ph.D. Computer Science", "M.Tech"],
  department: "Computer Science",
  subjects: ["Data Structures", "Algorithms"],
  schoolId: "sch_1",
};

describe("Unit: useTeacherStore", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useTeacherStore.getState().reset();
  });

  it("fetchTeacherMe populates teacher data on success", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockTeacher });

    await useTeacherStore.getState().fetchTeacherMe();

    expect(api.get).toHaveBeenCalledWith("/api/v1/teachers/me");
    expect(useTeacherStore.getState().teacher).toEqual(mockTeacher);
    expect(useTeacherStore.getState().error).toBe("");
    expect(useTeacherStore.getState().loading).toBe(false);
  });

  it("fetchTeacherById loads specific faculty profile", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockTeacher });

    await useTeacherStore.getState().fetchTeacherById("tch_1");

    expect(api.get).toHaveBeenCalledWith("/api/v1/teachers/tch_1");
    expect(useTeacherStore.getState().teacher).toEqual(mockTeacher);
  });

  it("fetchTeachersBySchool loads roster of teachers", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [mockTeacher] });

    await useTeacherStore.getState().fetchTeachersBySchool("sch_1");

    expect(api.get).toHaveBeenCalledWith("/api/v1/teachers?schoolId=sch_1");
    expect(useTeacherStore.getState().teachers).toHaveLength(1);
  });

  it("updateTeacherMe successfully updates teacher profile", async () => {
    const updated = { ...mockTeacher, experience: 9 };
    vi.mocked(api.put).mockResolvedValueOnce({ data: updated });

    const result = await useTeacherStore
      .getState()
      .updateTeacherMe({ experience: 9 });

    expect(result).toBe(true);
    expect(api.put).toHaveBeenCalledWith("/api/v1/teachers/me", {
      experience: 9,
    });
    expect(useTeacherStore.getState().teacher?.experience).toBe(9);
  });

  it("handles errors gracefully and updates error state", async () => {
    vi.mocked(api.get).mockRejectedValueOnce({
      response: { data: { detail: "Profile not found" } },
    });

    await useTeacherStore.getState().fetchTeacherMe();

    expect(useTeacherStore.getState().teacher).toBeNull();
    expect(useTeacherStore.getState().error).toBe("Profile not found");
  });
});
