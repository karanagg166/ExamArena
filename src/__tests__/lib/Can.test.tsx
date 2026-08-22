import React from "react";
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { AbilityProvider, Can, useAbility } from "@/lib/casl";
import { useAuthStore } from "@/stores";
import type { User, UserRole } from "@/types/user";

function createMockUser(id: string, role: UserRole, email: string): User {
  return {
    id,
    name: `${role} User`,
    email,
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

function TestConsumer() {
  const ability = useAbility();
  return (
    <div>
      <div data-testid="can-create-exam">
        {ability.can("create", "Exam") ? "CAN_CREATE_EXAM" : "CANNOT_CREATE_EXAM"}
      </div>
      <Can I="create" a="Exam">
        <button data-testid="create-exam-btn">Create Exam</button>
      </Can>
      <Can I="manage" a="School">
        <button data-testid="manage-school-btn">Manage School</button>
      </Can>
      <Can I="start" a="Attempt">
        <button data-testid="start-attempt-btn">Start Attempt</button>
      </Can>
    </div>
  );
}

describe("CASL React Integration (<Can /> and AbilityProvider)", () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      loading: false,
    });
  });

  it("renders teacher UI controls according to permissions", () => {
    useAuthStore.setState({
      user: createMockUser("t1", "TEACHER", "teacher@test.com"),
    });

    render(
      <AbilityProvider>
        <TestConsumer />
      </AbilityProvider>
    );

    expect(screen.getByTestId("can-create-exam")).toHaveTextContent("CAN_CREATE_EXAM");
    expect(screen.getByTestId("create-exam-btn")).toBeInTheDocument();
    expect(screen.queryByTestId("manage-school-btn")).not.toBeInTheDocument();
    expect(screen.queryByTestId("start-attempt-btn")).not.toBeInTheDocument();
  });

  it("renders student UI controls according to permissions", () => {
    useAuthStore.setState({
      user: createMockUser("s1", "STUDENT", "student@test.com"),
    });

    render(
      <AbilityProvider>
        <TestConsumer />
      </AbilityProvider>
    );

    expect(screen.getByTestId("can-create-exam")).toHaveTextContent("CANNOT_CREATE_EXAM");
    expect(screen.queryByTestId("create-exam-btn")).not.toBeInTheDocument();
    expect(screen.queryByTestId("manage-school-btn")).not.toBeInTheDocument();
    expect(screen.getByTestId("start-attempt-btn")).toBeInTheDocument();
  });

  it("renders principal UI controls with school management permissions", () => {
    useAuthStore.setState({
      user: createMockUser("p1", "PRINCIPAL", "principal@test.com"),
    });

    render(
      <AbilityProvider>
        <TestConsumer />
      </AbilityProvider>
    );

    expect(screen.getByTestId("create-exam-btn")).toBeInTheDocument();
    expect(screen.getByTestId("manage-school-btn")).toBeInTheDocument();
    expect(screen.queryByTestId("start-attempt-btn")).not.toBeInTheDocument();
  });
});
