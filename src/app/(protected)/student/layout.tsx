import type { ReactNode } from "react";
import StudentNavbar from "@/components/navbars/StudentNavbar";

export default function StudentLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <StudentNavbar />
      {children}
    </>
  );
}
