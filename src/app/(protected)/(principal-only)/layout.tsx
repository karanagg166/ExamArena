import type { ReactNode } from "react";

export default function PrincipalOnlyLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <>{children}</>;
}
