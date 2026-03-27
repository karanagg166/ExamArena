"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/stores";

const BASE_LINK_CLS = "px-3 py-2 rounded-lg text-sm font-medium transition-colors";

function linkClass(isActive: boolean) {
    return `${BASE_LINK_CLS} ${isActive ? "bg-indigo-600 text-white" : "text-zinc-300 hover:bg-zinc-800 hover:text-white"}`;
}

export default function PrincipalNavbar() {
    const pathname = usePathname();
    const router = useRouter();
    const logout = useAuthStore((s) => s.logout);

    const handleLogout = async () => {
        await logout();
        router.push("/login");
    };

    return (
        <nav className="sticky top-0 z-20 border-b border-zinc-800 bg-black/90 backdrop-blur">
            <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
                <span className="text-xs font-semibold uppercase tracking-widest text-indigo-400">Principal</span>

                <div className="flex flex-wrap items-center gap-2">
                    <Link href="/dashboard" className={linkClass(pathname === "/dashboard")}>Dashboard</Link>
                    <Link href="/principal" className={linkClass(pathname === "/principal" || pathname.startsWith("/principal/profile"))}>Profile</Link>
                    <Link href="/principal/school/school-class" className={linkClass(pathname.startsWith("/principal/school/school-class"))}>Add Class</Link>
                    <Link href="/school" className={linkClass(pathname === "/school" || pathname.startsWith("/school/profile"))}>School</Link>
                    <button
                        onClick={handleLogout}
                        className="px-3 py-2 rounded-lg text-sm font-semibold bg-red-600 text-white hover:bg-red-500 transition-colors"
                    >
                        Logout
                    </button>
                </div>
            </div>
        </nav>
    );
}