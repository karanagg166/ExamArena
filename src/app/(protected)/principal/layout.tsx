import type { ReactNode } from "react";
import PrincipalNavbar from "@/components/PrincipalNavbar";

export default function PrincipalLayout({ children }: { children: ReactNode }) {
    return (
        <>
            <PrincipalNavbar />
            {children}
        </>
    );
}