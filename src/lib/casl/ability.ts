import { AbilityBuilder, createMongoAbility } from "@casl/ability";
import type { AppAbility, CaslUser } from "./types";

/**
 * Builds and returns a strongly-typed CASL Ability instance based on the current user's role.
 */
export function defineAbilityFor(user?: CaslUser | null): AppAbility {
  const { can, cannot, build } = new AbilityBuilder<AppAbility>(createMongoAbility);

  const rawRole = user?.role ? String(user.role).toUpperCase() : "";

  switch (rawRole) {
    case "ADMIN":
      // Admin has full management access over everything
      can("manage", "all");
      break;

    case "PRINCIPAL":
      // Principal manages school, staff, classes, exams, audit logs, chat, profile
      can("manage", "School");
      can("manage", "SchoolClass");
      can("manage", "Teacher");
      can("manage", "Student");
      can("manage", "Exam");
      can("manage", "Question");
      can("manage", "JoinRequest");
      can("read", "AuditLog");
      can("read", "Attempt");
      can("manage", "Profile");
      can("manage", "Chat");
      // Principals do not take student attempts
      cannot("start", "Attempt");
      break;

    case "TEACHER":
      // Teacher authors exams, manages questions, views classes, reviews attempts
      can("manage", "Exam");
      can("manage", "Question");
      can("read", "SchoolClass");
      can("update", "SchoolClass");
      can("read", "Student");
      can("read", "Teacher");
      can("manage", "JoinRequest");
      can("read", "School");
      can("join", "School");
      can("read", "Attempt");
      can("manage", "Profile");
      can("manage", "Chat");
      // Teachers cannot take exams as students or view admin audit logs
      cannot("start", "Attempt");
      cannot("read", "AuditLog");
      cannot("create", "School");
      break;

    case "STUDENT":
      // Student browses exams, takes attempts, joins classes, chats
      can("read", "Exam");
      can("start", "Exam");
      can("start", "Attempt");
      can("submit", "Attempt");
      can("read", "Attempt");
      can("read", "SchoolClass");
      can("join", "SchoolClass");
      can("read", "Student");
      can("read", "Teacher");
      can("read", "School");
      can("create", "JoinRequest");
      can("manage", "Profile");
      can("manage", "Chat");
      // Students cannot author or modify exams/schools
      cannot("create", "Exam");
      cannot("update", "Exam");
      cannot("delete", "Exam");
      cannot("create", "School");
      cannot("create", "Question");
      cannot("read", "AuditLog");
      break;

    default:
      // Unauthenticated / Guest: read-only access to public exams
      can("read", "Exam");
      break;
  }

  return build();
}
