"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  User,
  School,
  GraduationCap,
  BookOpen,
  ClipboardList,
  Plus,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Users,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores";
import type { UserRole } from "@/types/user";

/* ─── Nav item config per role ─── */

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  /** Match paths starting with this prefix */
  matchPrefix?: string;
}

const navItemsByRole: Record<UserRole, NavItem[]> = {
  PRINCIPAL: [
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    {
      label: "My School",
      href: "/principal/school",
      icon: School,
      matchPrefix: "/principal/school",
    },
    {
      label: "Classes",
      href: "/principal/school/classes",
      icon: GraduationCap,
      matchPrefix: "/principal/school/classes",
    },
    {
      label: "Profile",
      href: "/principal/profile",
      icon: User,
      matchPrefix: "/principal/profile",
    },
  ],
  TEACHER: [
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    {
      label: "My Classes",
      href: "/teacher/classes",
      icon: GraduationCap,
      matchPrefix: "/teacher/classes",
    },
    {
      label: "Create Exam",
      href: "/teacher/exams/create",
      icon: Plus,
      matchPrefix: "/teacher/exams/create",
    },
    {
      label: "Exams",
      href: "/teacher/exams",
      icon: ClipboardList,
      matchPrefix: "/teacher/exams",
    },
    {
      label: "Profile",
      href: "/teacher/profile",
      icon: User,
      matchPrefix: "/teacher/profile",
    },
  ],
  STUDENT: [
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    {
      label: "My School",
      href: "/student/school",
      icon: School,
      matchPrefix: "/student/school",
    },
    {
      label: "My Class",
      href: "/student/class",
      icon: GraduationCap,
      matchPrefix: "/student/class",
    },
    {
      label: "Take Exam",
      href: "/student/exams/take",
      icon: BookOpen,
      matchPrefix: "/student/exams/take",
    },
    {
      label: "Results",
      href: "/student/exams/history",
      icon: ClipboardList,
      matchPrefix: "/student/exams/history",
    },
    {
      label: "Profile",
      href: "/student/profile",
      icon: User,
      matchPrefix: "/student/profile",
    },
  ],
  ADMIN: [
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { label: "Schools", href: "/schools", icon: School, matchPrefix: "/schools" },
    { label: "Users", href: "/admin/users", icon: Users, matchPrefix: "/admin/users" },
    { label: "Profile", href: "/profile", icon: User, matchPrefix: "/profile" },
  ],
};

/* ─── Role badge colors ─── */
const roleBadgeColors: Record<UserRole, string> = {
  PRINCIPAL: "border-violet-500/25 bg-violet-500/10 text-violet-300",
  TEACHER: "border-emerald-500/25 bg-emerald-500/10 text-emerald-300",
  STUDENT: "border-sky-500/25 bg-sky-500/10 text-sky-300",
  ADMIN: "border-amber-500/25 bg-amber-500/10 text-amber-300",
};

/* ─── Sidebar component ─── */

export function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [collapsed, setCollapsed] = useState(false);

  if (!user) return null;

  const role = user.role;
  const navItems = navItemsByRole[role] || [];

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const isActive = (item: NavItem) => {
    if (item.matchPrefix) return pathname.startsWith(item.matchPrefix);
    return pathname === item.href;
  };

  return (
    <>
      {/* ─── Desktop Sidebar ─── */}
      <aside
        className={cn(
          "glass-nav fixed inset-y-0 left-0 z-30 hidden flex-col border-r border-[var(--border-subtle)] transition-all duration-300 md:flex",
          collapsed ? "w-[68px]" : "w-[240px]",
        )}
      >
        {/* Logo / Brand */}
        <div className="flex h-14 items-center gap-3 border-b border-[var(--border-subtle)] px-4">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--accent)] text-sm font-bold text-white">
            EA
          </div>
          {!collapsed && (
            <span className="text-sm font-semibold text-[var(--text-primary)] animate-fade-in">
              Exam Arena
            </span>
          )}
        </div>

        {/* Role Badge */}
        <div className="px-3 pt-4 pb-2">
          {!collapsed ? (
            <span
              className={cn(
                "inline-flex rounded-full border px-3 py-1 text-[10px] font-semibold uppercase tracking-widest",
                roleBadgeColors[role],
              )}
            >
              {role}
            </span>
          ) : (
            <div
              className={cn(
                "mx-auto h-2 w-2 rounded-full",
                role === "PRINCIPAL" && "bg-violet-400",
                role === "TEACHER" && "bg-emerald-400",
                role === "STUDENT" && "bg-sky-400",
                role === "ADMIN" && "bg-amber-400",
              )}
            />
          )}
        </div>

        {/* Nav Items */}
        <nav className="flex-1 space-y-1 px-3 py-2 overflow-y-auto">
          {navItems.map((item) => {
            const active = isActive(item);
            return (
              <Link
                key={item.href}
                href={item.href}
                title={collapsed ? item.label : undefined}
                className={cn(
                  "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
                  active
                    ? "bg-[var(--accent-muted)] text-[var(--accent)] shadow-sm"
                    : "text-[var(--text-muted)] hover:bg-[var(--surface-2)] hover:text-[var(--text-primary)]",
                  collapsed && "justify-center px-2",
                )}
              >
                <item.icon
                  className={cn(
                    "h-[18px] w-[18px] shrink-0 transition-colors",
                    active
                      ? "text-[var(--accent)]"
                      : "text-[var(--text-muted)] group-hover:text-[var(--text-primary)]",
                  )}
                />
                {!collapsed && (
                  <span className="animate-fade-in">{item.label}</span>
                )}
                {/* Active indicator pill */}
                {active && !collapsed && (
                  <div className="ml-auto h-1.5 w-1.5 rounded-full bg-[var(--accent)]" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Bottom section */}
        <div className="border-t border-[var(--border-subtle)] p-3 space-y-2">
          {/* User info */}
          {!collapsed && (
            <div className="rounded-xl bg-[var(--surface-2)] px-3 py-2.5 animate-fade-in">
              <p className="truncate text-sm font-medium text-[var(--text-primary)]">
                {user.name}
              </p>
              <p className="truncate text-xs text-[var(--text-muted)]">
                {user.email}
              </p>
            </div>
          )}

          {/* Logout */}
          <button
            onClick={handleLogout}
            title={collapsed ? "Logout" : undefined}
            className={cn(
              "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-[var(--error)] transition-all hover:bg-[var(--error-muted)]",
              collapsed && "justify-center px-2",
            )}
          >
            <LogOut className="h-[18px] w-[18px] shrink-0" />
            {!collapsed && <span>Logout</span>}
          </button>

          {/* Collapse toggle */}
          <button
            onClick={() => setCollapsed((c) => !c)}
            className="flex w-full items-center justify-center rounded-xl py-1.5 text-[var(--text-dimmed)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text-primary)]"
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </button>
        </div>
      </aside>

      {/* ─── Mobile Bottom Tab Bar ─── */}
      <nav className="glass-nav fixed inset-x-0 bottom-0 z-30 flex border-t border-[var(--border-subtle)] md:hidden">
        {navItems.slice(0, 5).map((item) => {
          const active = isActive(item);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-1 flex-col items-center gap-0.5 py-2 text-[10px] font-medium transition-colors",
                active
                  ? "text-[var(--accent)]"
                  : "text-[var(--text-muted)]",
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </>
  );
}

/* ─── Layout wrapper that adds sidebar spacing ─── */

export function SidebarLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <AppSidebar />
      {/* Main content area — offset by sidebar width */}
      <main className="flex-1 md:ml-[240px] pb-16 md:pb-0">
        {children}
      </main>
    </div>
  );
}
