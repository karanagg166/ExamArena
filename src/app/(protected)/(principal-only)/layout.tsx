import type { ReactNode } from "react";
import { RoleGuard } from "@/components/auth/RoleGuard";

export default function PrincipalOnlyLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <RoleGuard allowedRoles={["PRINCIPAL", "ADMIN"]}>{children}</RoleGuard>;
}
