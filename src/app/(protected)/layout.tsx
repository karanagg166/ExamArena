import type { ReactNode } from "react";
import { SidebarLayout } from "@/components/navbars/AppSidebar";

export default function ProtectedLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <SidebarLayout>{children}</SidebarLayout>;
}
