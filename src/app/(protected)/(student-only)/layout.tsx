import type { ReactNode } from "react";
import { RoleGuard } from "@/components/auth/RoleGuard";

export default function StudentOnlyLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <RoleGuard allowedRoles={["STUDENT", "ADMIN"]}>{children}</RoleGuard>;
}
