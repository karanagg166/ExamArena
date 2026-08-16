"use client";

import Link from "next/link";
import { useAuthStore } from "@/stores/useAuthStore";
import {
  School,
  Users,
  UserCircle,
  ArrowRight,
  Plus,
  ClipboardList,
  UserCheck,
  GraduationCap,
  BookOpen,
  Award,
} from "lucide-react";
import { PageHeader } from "@/components/ui/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function PrincipalDashboard() {
  const { user } = useAuthStore();

  const links = [
    {
      title: "Teacher & Student Requests",
      description:
        "Review incoming faculty join requests, teaching class assignments, and student enrollment approvals in real-time.",
      href: "/principal/teacher-requests",
      icon: UserCheck,
      color: "text-amber-400",
      bg: "bg-amber-500/15",
      hoverBg: "group-hover:bg-amber-500",
      badge: "Action Required",
      badgeVariant: "warning" as const,
    },
    {
      title: "Classes & Join Codes",
      description:
        "Oversee all classes, generate student join codes, assign faculty, and inspect class exam performance.",
      href: "/principal/school/classes",
      icon: GraduationCap,
      color: "text-emerald-400",
      bg: "bg-emerald-500/15",
      hoverBg: "group-hover:bg-emerald-500",
      badge: "Classes & Rosters",
      badgeVariant: "default" as const,
    },
    {
      title: "Create Assessment / Exam",
      description:
        "Build school-wide assessments, midterms, quizzes, and mock tests with custom sections and negative marks.",
      href: "/teacher/exams/create",
      icon: Plus,
      color: "text-indigo-400",
      bg: "bg-indigo-500/15",
      hoverBg: "group-hover:bg-indigo-500",
    },
    {
      title: "School Exams & Scoreboards",
      description:
        "Manage created exams, evaluate submissions, inspect student leaderboards, and release scorecards.",
      href: "/teacher/exams",
      icon: ClipboardList,
      color: "text-blue-400",
      bg: "bg-blue-500/15",
      hoverBg: "group-hover:bg-blue-500",
    },
    {
      title: "Students Directory",
      description:
        "Inspect all enrolled students, roll numbers, contact records, and complete historical exam scorecards.",
      href: "/students",
      icon: Users,
      color: "text-violet-400",
      bg: "bg-violet-500/15",
      hoverBg: "group-hover:bg-violet-500",
    },
    {
      title: "Faculty Directory",
      description:
        "Browse all active teachers, view assigned departments, subjects taught, and contact details.",
      href: "/teachers",
      icon: BookOpen,
      color: "text-pink-400",
      bg: "bg-pink-500/15",
      hoverBg: "group-hover:bg-pink-500",
    },
    {
      title: "School Profile & Details",
      description:
        "Manage your school's core identity, registration code, address, and administration settings.",
      href: "/principal/school",
      icon: School,
      color: "text-cyan-400",
      bg: "bg-cyan-500/15",
      hoverBg: "group-hover:bg-cyan-500",
    },
    {
      title: "Principal Profile",
      description:
        "Update your administrative credentials, leadership credentials, and contact info.",
      href: "/principal/profile",
      icon: UserCircle,
      color: "text-[var(--warning)]",
      bg: "bg-[var(--warning-muted)]",
      hoverBg: "group-hover:bg-[var(--warning)]",
    },
  ];

  return (
    <div className="page-shell">
      <div className="max-w-6xl mx-auto space-y-8 animate-fade-in-up">
        {/* Header Section */}
        <div className="glass-card p-6 md:p-10 relative overflow-hidden rounded-3xl border border-[var(--border-default)]">
          <div className="absolute inset-0 bg-gradient-to-br from-violet-600/10 via-transparent to-amber-600/10" />
          <div className="absolute top-0 right-0 p-8 opacity-[0.04] pointer-events-none">
            <School size={180} />
          </div>
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <PageHeader
                overline="Principal Command Center"
                title={`Welcome back, ${user?.name?.split(" ")[0] || "Principal"}! 👋`}
                subtitle="Your school administration hub. Approve incoming teacher and student requests, oversee class rosters, manage exam scoreboards, and update institutional details."
              />
            </div>
            <div className="flex flex-wrap items-center gap-2.5 shrink-0">
              <Link href="/principal/teacher-requests">
                <Button size="sm" className="bg-amber-500 hover:bg-amber-600 text-white shadow-sm">
                  <UserCheck className="w-4 h-4 mr-1.5" /> Review Requests
                </Button>
              </Link>
              <Link href="/principal/school/classes">
                <Button size="sm" variant="secondary">
                  <GraduationCap className="w-4 h-4 mr-1.5" /> Classes & Roster
                </Button>
              </Link>
              <Link href="/teacher/exams">
                <Button size="sm" variant="outline">
                  <Award className="w-4 h-4 mr-1.5" /> Exam Results
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Priority Action Callout Banner */}
        <div className="rounded-2xl border border-amber-500/30 bg-amber-950/20 p-5 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-2xl bg-amber-500/15 text-amber-400">
              <UserCheck className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">
                Faculty Join & Student Admission Queue
              </h3>
              <p className="text-xs sm:text-sm text-zinc-400 mt-0.5">
                Review and decide teacher join requests, class teaching assignments, and student enrollment applications with one click.
              </p>
            </div>
          </div>
          <Link href="/principal/teacher-requests" className="shrink-0">
            <Button size="sm" className="bg-amber-500 hover:bg-amber-600 text-white">
              Open Requests Hub <ArrowRight className="w-4 h-4 ml-1.5" />
            </Button>
          </Link>
        </div>

        {/* Quick Links Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {links.map((link, i) => {
            const Icon = link.icon;
            return (
              <Link
                key={link.title}
                href={link.href}
                className={`group block animate-fade-in-up stagger-${i + 1}`}
              >
                <GlassCard interactive padding="md" className="h-full flex flex-col justify-between space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div
                        className={`p-3 rounded-2xl ${link.bg} ${link.color} ${link.hoverBg} group-hover:text-white transition-all group-hover:scale-110`}
                      >
                        <Icon size={22} />
                      </div>
                      {link.badge ? (
                        <Badge
                          variant={link.badgeVariant}
                          className="text-[10px] uppercase tracking-wider font-semibold"
                        >
                          {link.badge}
                        </Badge>
                      ) : (
                        <ArrowRight className="w-4 h-4 text-[var(--text-dimmed)] group-hover:text-[var(--text-secondary)] transition-colors" />
                      )}
                    </div>
                    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1.5 group-hover:text-amber-400 transition-colors">
                      {link.title}
                    </h3>
                    <p className="text-sm text-[var(--text-muted)] leading-relaxed">
                      {link.description}
                    </p>
                  </div>

                  <div className="flex items-center text-xs font-semibold text-amber-400 group-hover:text-amber-300 pt-1">
                    Open <ArrowRight className="w-3.5 h-3.5 ml-1 transition-transform group-hover:translate-x-1" />
                  </div>
                </GlassCard>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
