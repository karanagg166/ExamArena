"use client";

import Link from "next/link";
import { useAuthStore } from "@/stores/useAuthStore";
import {
  GraduationCap,
  Building2,
  UserCircle,
  ArrowRight,
  School,
  ClipboardList,
  Plus,
  Users,
  BookOpen,
  UserCheck,
} from "lucide-react";
import { PageHeader } from "@/components/ui/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function TeacherDashboard() {
  const { user } = useAuthStore();

  const links = [
    {
      title: "Student Join Requests",
      description:
        "Review and accept incoming student enrollment applications for your classes.",
      href: "/teacher/requests?tab=students",
      icon: UserCheck,
      color: "text-emerald-400",
      bg: "bg-emerald-500/15",
      hoverBg: "group-hover:bg-emerald-500",
      badge: "Student Queue",
      badgeVariant: "success" as const,
    },
    {
      title: "Join a School / Status",
      description:
        "Browse registered schools to join or track your faculty membership approval status.",
      href: "/teacher/requests?tab=school",
      icon: School,
      color: "text-amber-400",
      bg: "bg-amber-500/15",
      hoverBg: "group-hover:bg-amber-500",
      badge: "School Join",
      badgeVariant: "warning" as const,
    },
    {
      title: "My Classes & Join Codes",
      description:
        "View assigned classes, copy 8-character student enrollment codes, and manage rosters.",
      href: "/teacher/classes",
      icon: GraduationCap,
      color: "text-indigo-400",
      bg: "bg-indigo-500/15",
      hoverBg: "group-hover:bg-indigo-500",
      badge: "Classes & Roster",
      badgeVariant: "default" as const,
    },
    {
      title: "Create New Exam",
      description:
        "Draft assessments with custom sections, question types, timers, marks, and negative marking rules.",
      href: "/teacher/exams/create",
      icon: Plus,
      color: "text-sky-400",
      bg: "bg-sky-500/15",
      hoverBg: "group-hover:bg-sky-500",
    },
    {
      title: "Exams, Results & Leaderboards",
      description:
        "Inspect student leaderboards, grade responses, analyze pass rates, and release scorecards.",
      href: "/teacher/exams",
      icon: ClipboardList,
      color: "text-blue-400",
      bg: "bg-blue-500/15",
      hoverBg: "group-hover:bg-blue-500",
    },
    {
      title: "Students Directory",
      description:
        "Search students across your school, inspect roll numbers, and view complete student score records.",
      href: "/students",
      icon: Users,
      color: "text-violet-400",
      bg: "bg-violet-500/15",
      hoverBg: "group-hover:bg-violet-500",
    },
    {
      title: "School Directory",
      description:
        "Access administrative information and contact details for your current institution.",
      href: "/teacher/school",
      icon: Building2,
      color: "text-pink-400",
      bg: "bg-pink-500/15",
      hoverBg: "group-hover:bg-pink-500",
    },
    {
      title: "Faculty Directory",
      description:
        "Connect with fellow department teachers, view subjects taught, and coordinate curricula.",
      href: "/teachers",
      icon: BookOpen,
      color: "text-teal-400",
      bg: "bg-teal-500/15",
      hoverBg: "group-hover:bg-teal-500",
    },
    {
      title: "My Qualifications & Profile",
      description:
        "Update your teaching subjects, experience, degrees, and professional contact info.",
      href: "/teacher/profile",
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
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-600/10 via-transparent to-indigo-600/10" />
          <div className="absolute top-0 right-0 p-8 opacity-[0.04] pointer-events-none">
            <GraduationCap size={180} />
          </div>
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <PageHeader
                overline="Teacher Command Center"
                title={`Welcome back, ${user?.name?.split(" ")[0] || "Teacher"}! 👋`}
                subtitle="Manage student class join requests, track your school join status, draft exams, and release student scoreboards."
              />
            </div>
            <div className="flex flex-wrap items-center gap-2 shrink-0">
              <Link href="/teacher/requests?tab=students">
                <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm text-xs">
                  <UserCheck className="w-3.5 h-3.5 mr-1" /> Student Requests
                </Button>
              </Link>
              <Link href="/teacher/requests?tab=school">
                <Button size="sm" className="bg-amber-500 hover:bg-amber-600 text-white shadow-sm text-xs">
                  <School className="w-3.5 h-3.5 mr-1" /> Join School
                </Button>
              </Link>
              <Link href="/teacher/exams/create">
                <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm text-xs">
                  <Plus className="w-3.5 h-3.5 mr-1" /> Create Exam
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Action Callout Ribbons */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 rounded-2xl border border-emerald-500/30 bg-emerald-950/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-emerald-500/15 text-emerald-400">
                <UserCheck className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">Student Enrollment Requests</h4>
                <p className="text-xs text-zinc-400">Review students who entered your class join code.</p>
              </div>
            </div>
            <Link href="/teacher/requests?tab=students" className="shrink-0">
              <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs">
                Accept Requests <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </Button>
            </Link>
          </div>

          <div className="p-4 rounded-2xl border border-amber-500/30 bg-amber-950/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-amber-500/15 text-amber-400">
                <School className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">School Join Requests & Status</h4>
                <p className="text-xs text-zinc-400">Browse schools or track your faculty membership status.</p>
              </div>
            </div>
            <Link href="/teacher/requests?tab=school" className="shrink-0">
              <Button size="sm" className="bg-amber-500 hover:bg-amber-600 text-white text-xs">
                Join a School <ArrowRight className="w-3.5 h-3.5 ml-1" />
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
                className={`group block animate-fade-in-up stagger-${Math.min(i + 1, 6)}`}
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
                    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1.5 group-hover:text-indigo-400 transition-colors">
                      {link.title}
                    </h3>
                    <p className="text-sm text-[var(--text-muted)] leading-relaxed">
                      {link.description}
                    </p>
                  </div>

                  <div className="flex items-center text-xs font-semibold text-indigo-400 group-hover:text-indigo-300 pt-1">
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
