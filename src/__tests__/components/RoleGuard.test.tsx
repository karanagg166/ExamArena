import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { useAuthStore } from "@/stores";
import type { User, UserRole } from "@/types/user";

const mockReplace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: mockReplace,
    push: vi.fn(),
  }),
}));

function createMockUser(id: string, role: UserRole): User {
  return {
    id,
    name: `${role} User`,
    email: `${role.toLowerCase()}@test.com`,
    phoneNo: "9999999999",
    dateOfBirth: "2000-01-01",
    role,
    pincode: "110001",
    city: "New Delhi",
    state: "Delhi",
    country: "India",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

describe("RoleGuard UX Guard Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.setState({ user: null, loading: false, error: null });
  });

  it("shows loading indicator while authorization is checking", () => {
    useAuthStore.setState({ user: null, loading: true });
    render(
      <RoleGuard allowedRoles={["TEACHER"]}>
        <div>Protected Content</div>
      </RoleGuard>
    );

    expect(screen.getByText("Loading authorization...")).toBeDefined();
    expect(screen.queryByText("Protected Content")).toBeNull();
  });

  it("redirects unauthenticated users to /login", () => {
    useAuthStore.setState({ user: null, loading: false });
    render(
      <RoleGuard allowedRoles={["TEACHER"]}>
        <div>Protected Content</div>
      </RoleGuard>
    );

    expect(mockReplace).toHaveBeenCalledWith("/login");
    expect(screen.queryByText("Protected Content")).toBeNull();
  });

  it("redirects unauthorized users to /dashboard", () => {
    useAuthStore.setState({
      user: createMockUser("u_student", "STUDENT"),
      loading: false,
    });

    render(
      <RoleGuard allowedRoles={["TEACHER", "ADMIN"]}>
        <div>Teacher Only Section</div>
      </RoleGuard>
    );

    expect(mockReplace).toHaveBeenCalledWith("/dashboard");
    expect(screen.queryByText("Teacher Only Section")).toBeNull();
  });

  it("renders children when user role is allowed", () => {
    useAuthStore.setState({
      user: createMockUser("u_teacher", "TEACHER"),
      loading: false,
    });

    render(
      <RoleGuard allowedRoles={["TEACHER", "ADMIN"]}>
        <div>Teacher Only Section</div>
      </RoleGuard>
    );

    expect(screen.getByText("Teacher Only Section")).toBeDefined();
    expect(mockReplace).not.toHaveBeenCalled();
  });
});
