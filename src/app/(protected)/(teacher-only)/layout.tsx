import type { ReactNode } from "react";

export default function TeacherOnlyLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <>{children}</>;
}
