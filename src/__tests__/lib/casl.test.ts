import { describe, it, expect } from "vitest";
import { defineAbilityFor } from "@/lib/casl";

describe("CASL Role-Based Access Control", () => {
  describe("ADMIN Role", () => {
    const adminUser = { id: "1", email: "admin@example.com", role: "ADMIN" };
    const ability = defineAbilityFor(adminUser);

    it("allows full management of all resources", () => {
      expect(ability.can("manage", "all")).toBe(true);
      expect(ability.can("create", "Exam")).toBe(true);
      expect(ability.can("delete", "School")).toBe(true);
      expect(ability.can("read", "AuditLog")).toBe(true);
    });
  });

  describe("PRINCIPAL Role", () => {
    const principalUser = { id: "2", email: "principal@example.com", role: "PRINCIPAL" };
    const ability = defineAbilityFor(principalUser);

    it("allows managing schools, classes, staff, exams, and audit logs", () => {
      expect(ability.can("manage", "School")).toBe(true);
      expect(ability.can("manage", "SchoolClass")).toBe(true);
      expect(ability.can("manage", "Teacher")).toBe(true);
      expect(ability.can("manage", "Student")).toBe(true);
      expect(ability.can("manage", "Exam")).toBe(true);
      expect(ability.can("read", "AuditLog")).toBe(true);
    });

    it("disallows taking student exam attempts", () => {
      expect(ability.can("start", "Attempt")).toBe(false);
    });
  });

  describe("TEACHER Role", () => {
    const teacherUser = { id: "3", email: "teacher@example.com", role: "TEACHER" };
    const ability = defineAbilityFor(teacherUser);

    it("allows managing exams, questions, and viewing classes", () => {
      expect(ability.can("manage", "Exam")).toBe(true);
      expect(ability.can("create", "Exam")).toBe(true);
      expect(ability.can("manage", "Question")).toBe(true);
      expect(ability.can("read", "SchoolClass")).toBe(true);
      expect(ability.can("update", "SchoolClass")).toBe(true);
      expect(ability.can("join", "School")).toBe(true);
    });

    it("disallows creating schools, reading audit logs, or starting attempts", () => {
      expect(ability.can("create", "School")).toBe(false);
      expect(ability.can("read", "AuditLog")).toBe(false);
      expect(ability.can("start", "Attempt")).toBe(false);
    });
  });

  describe("STUDENT Role", () => {
    const studentUser = { id: "4", email: "student@example.com", role: "STUDENT" };
    const ability = defineAbilityFor(studentUser);

    it("allows reading exams, starting attempts, and joining classes", () => {
      expect(ability.can("read", "Exam")).toBe(true);
      expect(ability.can("start", "Exam")).toBe(true);
      expect(ability.can("start", "Attempt")).toBe(true);
      expect(ability.can("submit", "Attempt")).toBe(true);
      expect(ability.can("join", "SchoolClass")).toBe(true);
      expect(ability.can("create", "JoinRequest")).toBe(true);
    });

    it("disallows authoring exams, managing schools, or accessing audit logs", () => {
      expect(ability.can("create", "Exam")).toBe(false);
      expect(ability.can("update", "Exam")).toBe(false);
      expect(ability.can("delete", "Exam")).toBe(false);
      expect(ability.can("create", "School")).toBe(false);
      expect(ability.can("read", "AuditLog")).toBe(false);
    });
  });

  describe("Unauthenticated / Guest", () => {
    const ability = defineAbilityFor(null);

    it("only permits reading public exams", () => {
      expect(ability.can("read", "Exam")).toBe(true);
      expect(ability.can("create", "Exam")).toBe(false);
      expect(ability.can("start", "Attempt")).toBe(false);
      expect(ability.can("manage", "School")).toBe(false);
    });
  });
});
