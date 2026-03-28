import type { ReactNode } from "react";
import TeacherNavbar from "@/components/TeacherNavbar";

export default function TeacherLayout({ children }: { children: ReactNode }) {
    return (
        <>
            <TeacherNavbar />
            {children}
        </>
    );
}