import type { MongoAbility } from "@casl/ability";
import type { UserRole } from "@/types/user";

export type AppAction =
  | "manage"
  | "create"
  | "read"
  | "update"
  | "delete"
  | "start"
  | "submit"
  | "join"
  | "approve"
  | "reject"
  | "view_audit";

export type AppSubject =
  | "all"
  | "Exam"
  | "Question"
  | "Attempt"
  | "School"
  | "SchoolClass"
  | "Student"
  | "Teacher"
  | "Principal"
  | "JoinRequest"
  | "AuditLog"
  | "Profile"
  | "Chat";

export type AppAbility = MongoAbility<[AppAction, AppSubject]>;

export interface CaslUser {
  id?: string;
  email?: string;
  role?: UserRole | string | null;
  name?: string;
}
