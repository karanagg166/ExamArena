import type { ReactNode } from "react";
import { RoleGuard } from "@/components/auth/RoleGuard";

export default function StaffOnlyLayout({ children }: { children: ReactNode }) {
  return (
    <RoleGuard allowedRoles={["TEACHER", "PRINCIPAL", "ADMIN"]}>
      {children}
    </RoleGuard>
  );
}
