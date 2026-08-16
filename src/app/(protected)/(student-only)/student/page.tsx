"use client";

import Link from "next/link";
import { useAuthStore } from "@/stores/useAuthStore";
import {
  Users,
  School,
  UserCircle,
  ArrowRight,
  GraduationCap,
  Award,
  Search,
  Settings,
  Sparkles,
} from "lucide-react";
import { PageHeader } from "@/components/ui/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function StudentDashboard() {
  const { user } = useAuthStore();

  const links = [
    {
      title: "My Exams & Results",
      description:
        "Check completed test scorecards, marks obtained, percentage, class rank, and released answer keys.",
      href: "/student/exams",
      icon: Award,
      color: "text-sky-400",
      bg: "bg-sky-500/15",
      hoverBg: "group-hover:bg-sky-500",
      badge: "Scores & Rank",
      badgeVariant: "info" as const,
    },
    {
      title: "Browse & Take Exams",
      description:
        "Find scheduled assessments, enter private exam codes, and complete timed tests with auto-grading.",
      href: "/exams",
      icon: Search,
      color: "text-indigo-400",
      bg: "bg-indigo-500/15",
      hoverBg: "group-hover:bg-indigo-500",
      badge: "Live Tests",
      badgeVariant: "default" as const,
    },
    {
      title: "My Class & Teachers",
      description:
        "View your assigned class section, teachers, class join codes, and classmates list.",
      href: "/student/class",
      icon: GraduationCap,
      color: "text-emerald-400",
      bg: "bg-emerald-500/15",
      hoverBg: "group-hover:bg-emerald-500",
    },
    {
      title: "Classmates Directory",
      description:
        "Explore and connect with peers and classmates enrolled across your school.",
      href: "/students",
      icon: Users,
      color: "text-violet-400",
      bg: "bg-violet-500/15",
      hoverBg: "group-hover:bg-violet-500",
    },
    {
      title: "School Information",
      description:
        "Learn more about your school's administration, principal, and official contact details.",
      href: "/student/school",
      icon: School,
      color: "text-amber-400",
      bg: "bg-amber-500/15",
      hoverBg: "group-hover:bg-amber-500",
    },
    {
      title: "Enrollment & Join Codes",
      description:
        "Enter 8-character class join codes, check admission request status, and manage parent records.",
      href: "/student/profile",
      icon: UserCircle,
      color: "text-pink-400",
      bg: "bg-pink-500/15",
      hoverBg: "group-hover:bg-pink-500",
    },
    {
      title: "Account Settings",
      description:
        "Update your personal profile, phone number, address, and password security.",
      href: "/profile",
      icon: Settings,
      color: "text-zinc-400",
      bg: "bg-zinc-800",
      hoverBg: "group-hover:bg-zinc-700",
    },
  ];

  return (
    <div className="page-shell">
      <div className="max-w-6xl mx-auto space-y-8 animate-fade-in-up">
        {/* Header Section */}
        <div className="glass-card p-6 md:p-10 relative overflow-hidden rounded-3xl border border-[var(--border-default)]">
          <div className="absolute inset-0 bg-gradient-to-br from-sky-600/10 via-transparent to-[var(--accent)]/5" />
          <div className="absolute top-0 right-0 p-8 opacity-[0.04] pointer-events-none">
            <Users size={180} />
          </div>
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <PageHeader
                overline="Student Learning Center"
                title={`Welcome back, ${user?.name?.split(" ")[0] || "Student"}! 👋`}
                subtitle="Your personal academic command center. Take scheduled exams, review graded answer sheets, join classes with enrollment codes, and track your progress."
              />
            </div>
            <div className="flex flex-wrap items-center gap-2.5 shrink-0">
              <Link href="/exams">
                <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm">
                  <Sparkles className="w-4 h-4 mr-1.5" /> Take Exam
                </Button>
              </Link>
              <Link href="/student/exams">
                <Button size="sm" variant="secondary">
                  <Award className="w-4 h-4 mr-1.5" /> View Scores & Rank
                </Button>
              </Link>
              <Link href="/student/class">
                <Button size="sm" variant="outline">
                  <GraduationCap className="w-4 h-4 mr-1.5" /> My Class
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Action Callout Banner */}
        <div className="rounded-2xl border border-sky-500/30 bg-sky-950/20 p-5 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-2xl bg-sky-500/15 text-sky-400">
              <Award className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">
                Exam Scorecards & Class Leaderboards
              </h3>
              <p className="text-xs sm:text-sm text-zinc-400 mt-0.5">
                Check released test results, detailed question solutions, percentage scores, and your rank in class.
              </p>
            </div>
          </div>
          <Link href="/student/exams" className="shrink-0">
            <Button size="sm" className="bg-sky-600 hover:bg-sky-700 text-white">
              Open My Scorecards <ArrowRight className="w-4 h-4 ml-1.5" />
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
                    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1.5 group-hover:text-sky-400 transition-colors">
                      {link.title}
                    </h3>
                    <p className="text-sm text-[var(--text-muted)] leading-relaxed">
                      {link.description}
                    </p>
                  </div>

                  <div className="flex items-center text-xs font-semibold text-sky-400 group-hover:text-sky-300 pt-1">
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
