import type { ReactNode } from "react";
import { RoleGuard } from "@/components/auth/RoleGuard";

export default function TeacherOnlyLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <RoleGuard allowedRoles={["TEACHER", "ADMIN"]}>{children}</RoleGuard>;
}
