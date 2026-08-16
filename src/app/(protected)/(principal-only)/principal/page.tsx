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
} from "lucide-react";
import { PageHeader } from "@/components/ui/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function PrincipalDashboard() {
  const { user } = useAuthStore();

  const links = [
    {
      title: "Teacher Join Requests",
      description:
        "Review incoming faculty applications seeking to join your school.",
      href: "/principal/teacher-requests?tab=faculty",
      icon: UserCheck,
      color: "text-amber-400",
      bg: "bg-amber-500/15",
      hoverBg: "group-hover:bg-amber-500",
      badge: "Faculty Queue",
      badgeVariant: "warning" as const,
    },
    {
      title: "Student Admission Requests",
      description:
        "Review students enrolling into school classes using join codes with 1-click roll number assignment.",
      href: "/principal/teacher-requests?tab=students",
      icon: GraduationCap,
      color: "text-emerald-400",
      bg: "bg-emerald-500/15",
      hoverBg: "group-hover:bg-emerald-500",
      badge: "Student Queue",
      badgeVariant: "success" as const,
    },
    {
      title: "Class Teaching Requests",
      description:
        "Approve faculty requests to teach specific class sections and batches.",
      href: "/principal/teacher-requests?tab=teaching",
      icon: BookOpen,
      color: "text-indigo-400",
      bg: "bg-indigo-500/15",
      hoverBg: "group-hover:bg-indigo-500",
      badge: "Class Assign",
      badgeVariant: "default" as const,
    },
    {
      title: "Classes & Join Codes",
      description:
        "Oversee all classes, generate student join codes, assign faculty, and inspect class exam performance.",
      href: "/principal/school/classes",
      icon: GraduationCap,
      color: "text-sky-400",
      bg: "bg-sky-500/15",
      hoverBg: "group-hover:bg-sky-500",
    },
    {
      title: "Create Assessment / Exam",
      description:
        "Build school-wide assessments, midterms, quizzes, and mock tests with custom sections and negative marks.",
      href: "/teacher/exams/create",
      icon: Plus,
      color: "text-violet-400",
      bg: "bg-violet-500/15",
      hoverBg: "group-hover:bg-violet-500",
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
      color: "text-pink-400",
      bg: "bg-pink-500/15",
      hoverBg: "group-hover:bg-pink-500",
    },
    {
      title: "Faculty Directory",
      description:
        "Browse all active teachers, view assigned departments, subjects taught, and contact details.",
      href: "/teachers",
      icon: Users,
      color: "text-teal-400",
      bg: "bg-teal-500/15",
      hoverBg: "group-hover:bg-teal-500",
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
                subtitle="Your school administration hub. Direct buttons below let you review teacher join requests, approve student class admissions, and oversee exams."
              />
            </div>
            <div className="flex flex-wrap items-center gap-2 shrink-0">
              <Link href="/principal/teacher-requests?tab=faculty">
                <Button size="sm" className="bg-amber-500 hover:bg-amber-600 text-white shadow-sm text-xs">
                  <UserCheck className="w-3.5 h-3.5 mr-1" /> Teacher Requests
                </Button>
              </Link>
              <Link href="/principal/teacher-requests?tab=students">
                <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm text-xs">
                  <GraduationCap className="w-3.5 h-3.5 mr-1" /> Student Requests
                </Button>
              </Link>
              <Link href="/principal/school/classes">
                <Button size="sm" variant="secondary" className="text-xs">
                  <GraduationCap className="w-3.5 h-3.5 mr-1" /> Classes & Roster
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Priority Action Callout Ribbons */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-2xl border border-amber-500/30 bg-amber-950/20 flex flex-col justify-between space-y-2.5">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400">
                <UserCheck className="h-4 w-4" />
              </div>
              <span className="text-sm font-bold text-white">Teacher Join Requests</span>
            </div>
            <p className="text-xs text-zinc-400">Review faculty joining applications.</p>
            <Link href="/principal/teacher-requests?tab=faculty">
              <Button size="sm" className="w-full bg-amber-500 hover:bg-amber-600 text-white text-xs">
                Review Teachers <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </Button>
            </Link>
          </div>

          <div className="p-4 rounded-2xl border border-emerald-500/30 bg-emerald-950/20 flex flex-col justify-between space-y-2.5">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400">
                <GraduationCap className="h-4 w-4" />
              </div>
              <span className="text-sm font-bold text-white">Student Admissions</span>
            </div>
            <p className="text-xs text-zinc-400">Approve class join code requests.</p>
            <Link href="/principal/teacher-requests?tab=students">
              <Button size="sm" className="w-full bg-emerald-600 hover:bg-emerald-700 text-white text-xs">
                Review Students <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </Button>
            </Link>
          </div>

          <div className="p-4 rounded-2xl border border-indigo-500/30 bg-indigo-950/20 flex flex-col justify-between space-y-2.5">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400">
                <BookOpen className="h-4 w-4" />
              </div>
              <span className="text-sm font-bold text-white">Class Teaching</span>
            </div>
            <p className="text-xs text-zinc-400">Review class assignment requests.</p>
            <Link href="/principal/teacher-requests?tab=teaching">
              <Button size="sm" className="w-full bg-indigo-600 hover:bg-indigo-700 text-white text-xs">
                Review Teaching <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </Button>
            </Link>
          </div>
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
