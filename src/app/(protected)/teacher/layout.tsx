import type { ReactNode } from "react";
import TeacherNavbar from "@/components/navbars/TeacherNavbar";

export default function TeacherLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <TeacherNavbar />
      {children}
    </>
  );
}
