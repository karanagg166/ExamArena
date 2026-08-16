"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore, useSchoolStore } from "@/stores";
import { Building2 } from "lucide-react";

const BASE_LINK_CLS =
  "rounded-xl border px-3 py-2 text-sm font-medium transition-colors duration-200";

function linkClass(isActive: boolean) {
  return `${BASE_LINK_CLS} ${
    isActive
      ? "border-indigo-500/40 bg-indigo-500/20 text-indigo-200"
      : "border-zinc-800 bg-zinc-900/60 text-zinc-300 hover:border-zinc-700 hover:text-white"
  }`;
}

export default function TeacherNavbar() {
  const pathname = usePathname();
  const router = useRouter();
  const logout = useAuthStore((s) => s.logout);
  const { school, hasFetched, fetchSchool } = useSchoolStore();

  useEffect(() => {
    if (!hasFetched) fetchSchool();
  }, [hasFetched, fetchSchool]);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <nav className="sticky top-0 z-20 border-b border-zinc-800/80 bg-zinc-950/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-emerald-300">
            Teacher
          </span>
          {school && (
            <span className="hidden sm:flex items-center gap-1.5 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300">
              <Building2 className="h-3 w-3 text-indigo-400" />
              {school.name}
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Link
            href="/dashboard"
            className={linkClass(pathname === "/dashboard")}
          >
            Dashboard
          </Link>
          <Link
            href="/teacher/requests?tab=students"
            className={linkClass(pathname.startsWith("/teacher/requests"))}
          >
            Student Requests
          </Link>
          <Link
            href="/teacher/classes"
            className={linkClass(pathname.startsWith("/teacher/classes"))}
          >
            My Classes
          </Link>
          <Link
            href="/teacher/exams/create"
            className={linkClass(pathname.startsWith("/teacher/exams/create"))}
          >
            Create Exam
          </Link>
          <Link
            href="/teacher/exams"
            className={linkClass(
              pathname === "/teacher/exams" ||
                pathname.startsWith("/teacher/exams/history") ||
                pathname.includes("/results"),
            )}
          >
            Exams & Results
          </Link>
          {school ? (
            <Link
              href="/teacher/school"
              className={linkClass(pathname.startsWith("/teacher/school"))}
            >
              My School
            </Link>
          ) : (
            <Link
              href="/teacher/school/join"
              className={linkClass(pathname === "/teacher/school/join")}
            >
              Join School
            </Link>
          )}
          <Link
            href="/students"
            className={linkClass(pathname.startsWith("/students"))}
          >
            Students
          </Link>
          <Link
            href="/teacher/profile"
            className={linkClass(
              pathname === "/teacher" ||
                pathname.startsWith("/teacher/profile"),
            )}
          >
            Profile
          </Link>
          <Link
            href="/signup/principal"
            className="rounded-xl border border-amber-500/40 bg-amber-500/15 px-3 py-2 text-sm font-semibold text-amber-200 transition-colors hover:bg-amber-500/25"
          >
            Become Principal
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
