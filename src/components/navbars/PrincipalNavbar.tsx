"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/stores";

const BASE_LINK_CLS =
  "rounded-xl border px-3 py-2 text-sm font-medium transition-colors duration-200";

function linkClass(isActive: boolean) {
  return `${BASE_LINK_CLS} ${
    isActive
      ? "border-indigo-500/40 bg-indigo-500/20 text-indigo-200"
      : "border-zinc-800 bg-zinc-900/60 text-zinc-300 hover:border-zinc-700 hover:text-white"
  }`;
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
    <nav className="sticky top-0 z-20 border-b border-zinc-800/80 bg-zinc-950/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <span className="rounded-full border border-violet-500/25 bg-violet-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-violet-300">
          Principal
        </span>

        <div className="flex flex-wrap items-center gap-2">
          <Link
            href="/dashboard"
            className={linkClass(pathname === "/dashboard")}
          >
            Dashboard
          </Link>
          <Link
            href="/principal"
            className={linkClass(
              pathname === "/principal" ||
                pathname.startsWith("/principal/profile"),
            )}
          >
            Profile
          </Link>
          <Link
            href="/principal/school/school-class"
            className={linkClass(
              pathname.startsWith("/principal/school/school-class"),
            )}
          >
            Add Class
          </Link>
          <Link
            href="/school"
            className={linkClass(
              pathname === "/school" || pathname.startsWith("/school/profile"),
            )}
          >
            School
          </Link>
          <button
            onClick={handleLogout}
            className="rounded-xl border border-red-500/40 bg-red-500/15 px-3 py-2 text-sm font-semibold text-red-200 transition-colors hover:bg-red-500/25"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
