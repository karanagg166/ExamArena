import type { ReactNode } from "react";

export default function StudentOnlyLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <>{children}</>;
}
