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
  Search,
  BookOpen,
  Award,
} from "lucide-react";
import { PageHeader } from "@/components/ui/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function TeacherDashboard() {
  const { user } = useAuthStore();

  const links = [
    {
      title: "My Classes & Student Requests",
      description:
        "Manage assigned classes, approve pending student enrollment requests, and copy 8-character student join codes.",
      href: "/teacher/classes",
      icon: GraduationCap,
      color: "text-indigo-400",
      bg: "bg-indigo-500/15",
      hoverBg: "group-hover:bg-indigo-500",
      badge: "Classes & Requests",
      badgeVariant: "default" as const,
    },
    {
      title: "Create New Exam",
      description:
        "Draft assessments with custom sections, question types, timers, marks, and negative marking rules.",
      href: "/teacher/exams/create",
      icon: Plus,
      color: "text-emerald-400",
      bg: "bg-emerald-500/15",
      hoverBg: "group-hover:bg-emerald-500",
      badge: "Exam Creator",
      badgeVariant: "success" as const,
    },
    {
      title: "Exams, Results & Leaderboards",
      description:
        "Inspect student leaderboards, grade responses, analyze pass rates, and release scorecards to students.",
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
      title: "Browse Available Exams",
      description:
        "Explore all public and school-wide assessments published across the platform.",
      href: "/exams",
      icon: Search,
      color: "text-cyan-400",
      bg: "bg-cyan-500/15",
      hoverBg: "group-hover:bg-cyan-500",
    },
    {
      title: "School Directory",
      description:
        "Access administrative information and contact details for your current institution.",
      href: "/teacher/school",
      icon: Building2,
      color: "text-amber-400",
      bg: "bg-amber-500/15",
      hoverBg: "group-hover:bg-amber-500",
    },
    {
      title: "Join a School",
      description:
        "Browse available institutions and submit direct faculty join applications.",
      href: "/teacher/school/join",
      icon: School,
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
                subtitle="Ready to educate and evaluate? Manage your student class requests, draft exams with negative marking, and release student scoreboards."
              />
            </div>
            <div className="flex flex-wrap items-center gap-2.5 shrink-0">
              <Link href="/teacher/exams/create">
                <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm">
                  <Plus className="w-4 h-4 mr-1.5" /> Create Exam
                </Button>
              </Link>
              <Link href="/teacher/classes">
                <Button size="sm" variant="secondary">
                  <GraduationCap className="w-4 h-4 mr-1.5" /> Classes & Requests
                </Button>
              </Link>
              <Link href="/teacher/exams">
                <Button size="sm" variant="outline">
                  <Award className="w-4 h-4 mr-1.5" /> Results & Leaderboards
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Action Callout Banner */}
        <div className="rounded-2xl border border-indigo-500/30 bg-indigo-950/20 p-5 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-2xl bg-indigo-500/15 text-indigo-400">
              <GraduationCap className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">
                Class Join Codes & Enrollment Queue
              </h3>
              <p className="text-xs sm:text-sm text-zinc-400 mt-0.5">
                Students enrolling with your class join codes appear in your approval queue. Accept student requests to add them to your roster.
              </p>
            </div>
          </div>
          <Link href="/teacher/classes" className="shrink-0">
            <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white">
              Open My Classes <ArrowRight className="w-4 h-4 ml-1.5" />
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
