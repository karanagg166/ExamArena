"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/axios";
import { Badge } from "@/components/ui/badge";
import { GlassCard } from "@/components/ui/glass-card";
import { Spinner } from "@/components/ui/loading";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  Award,
  BookOpen,
  Building2,
  ClipboardList,
  GraduationCap,
  ListChecks,
  Plus,
  School,
  Search,
  Settings,
  Sparkles,
  UserCheck,
  UserCircle,
  Users,
} from "lucide-react";

type User = {
  name: string;
  role: "STUDENT" | "TEACHER" | "PRINCIPAL" | "ADMIN";
  email: string;
};

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/api/v1/auth/me")
      .then((r) => setUser(r.data))
      .catch(() => router.push("/login"))
      .finally(() => setLoading(false));
  }, [router]);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Spinner className="h-8 w-8 border-4" />
      </div>
    );
  }

  const role = user?.role ?? "STUDENT";

  return (
    <div className="page-shell space-y-8">
      <div className="mx-auto max-w-6xl animate-fade-in-up space-y-8">
        {/* Welcome Header */}
        <div className="glass-card p-6 md:p-10 relative overflow-hidden rounded-3xl border border-[var(--border-default)]">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-600/10 via-transparent to-violet-600/10" />
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Badge
                  variant={
                    role === "PRINCIPAL"
                      ? "default"
                      : role === "TEACHER"
                      ? "success"
                      : role === "ADMIN"
                      ? "warning"
                      : "default"
                  }
                  className="uppercase tracking-widest text-[11px] px-2.5 py-0.5"
                >
                  {role} Portal
                </Badge>
                <span className="text-xs text-[var(--text-muted)]">ExamArena Hub</span>
              </div>
              <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-[var(--text-primary)] tracking-tight">
                Welcome back, {user?.name ?? "Educator"} 👋
              </h1>
              <p className="mt-1 text-sm sm:text-base text-[var(--text-muted)] max-w-2xl">
                {role === "PRINCIPAL" &&
                  "Oversee your school, approve teacher & student requests, view class join codes, and inspect exam performance."}
                {role === "TEACHER" &&
                  "Create exams, manage student enrollment requests, configure negative marks, and track student results."}
                {role === "STUDENT" &&
                  "Take scheduled assessments, view results & rank, join classes with enrollment codes, and track your progress."}
                {role === "ADMIN" &&
                  "Platform administration, manage registered schools, teachers, students, and system exams."}
              </p>
            </div>

            {/* Quick Action Ribbon */}
            <div className="flex flex-wrap items-center gap-2.5 shrink-0">
              {role === "PRINCIPAL" && (
                <>
                  <Link href="/principal/teacher-requests">
                    <Button size="sm" className="bg-amber-500 hover:bg-amber-600 text-white shadow-sm">
                      <UserCheck className="w-4 h-4 mr-1.5" /> Review Requests
                    </Button>
                  </Link>
                  <Link href="/teacher/exams/create">
                    <Button size="sm" variant="secondary">
                      <Plus className="w-4 h-4 mr-1.5" /> Create Exam
                    </Button>
                  </Link>
                </>
              )}

              {role === "TEACHER" && (
                <>
                  <Link href="/teacher/exams/create">
                    <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm">
                      <Plus className="w-4 h-4 mr-1.5" /> Create Exam
                    </Button>
                  </Link>
                  <Link href="/teacher/classes">
                    <Button size="sm" variant="secondary">
                      <ListChecks className="w-4 h-4 mr-1.5" /> Student Requests
                    </Button>
                  </Link>
                </>
              )}

              {role === "STUDENT" && (
                <>
                  <Link href="/exams">
                    <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm">
                      <Sparkles className="w-4 h-4 mr-1.5" /> Take Exam
                    </Button>
                  </Link>
                  <Link href="/student/exams">
                    <Button size="sm" variant="secondary">
                      <Award className="w-4 h-4 mr-1.5" /> View Results & Marks
                    </Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>

        {/* ─── PRINCIPAL COMMAND CENTER ─── */}
        {role === "PRINCIPAL" && (
          <div className="space-y-8">
            {/* Primary Action Callout Banner */}
            <div className="rounded-2xl border border-amber-500/30 bg-amber-950/20 p-5 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-2xl bg-amber-500/15 text-amber-400">
                  <UserCheck className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">
                    Pending School & Faculty Requests
                  </h3>
                  <p className="text-xs sm:text-sm text-zinc-400 mt-0.5">
                    Review and decide teacher join requests, class teaching assignments, and student enrollment applications.
                  </p>
                </div>
              </div>
              <Link href="/principal/teacher-requests" className="shrink-0">
                <Button size="sm" className="bg-amber-500 hover:bg-amber-600 text-white">
                  Open Requests Hub <ArrowRight className="w-4 h-4 ml-1.5" />
                </Button>
              </Link>
            </div>

            {/* Principal Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              <DashboardCard
                title="School Requests & Approvals"
                description="Review incoming faculty join requests, teaching class assignments, and student enrollment approvals."
                href="/principal/teacher-requests"
                icon={UserCheck}
                color="text-amber-400"
                bg="bg-amber-500/15"
                badge="Action Required"
                badgeVariant="warning"
              />

              <DashboardCard
                title="Classes & Join Codes"
                description="Manage all classes, generate student join codes, assign faculty, and inspect class exam performance."
                href="/principal/school/classes"
                icon={GraduationCap}
                color="text-emerald-400"
                bg="bg-emerald-500/15"
              />

              <DashboardCard
                title="Create New Exam"
                description="Draft school-wide assessments, midterms, quizzes, and mock tests with custom sections and negative marking."
                href="/teacher/exams/create"
                icon={Plus}
                color="text-indigo-400"
                bg="bg-indigo-500/15"
              />

              <DashboardCard
                title="Exams, Results & Marks"
                description="Manage created exams, evaluate submissions, inspect student leaderboards, and release scorecards."
                href="/teacher/exams"
                icon={ClipboardList}
                color="text-blue-400"
                bg="bg-blue-500/15"
              />

              <DashboardCard
                title="Students Directory"
                description="Search enrolled students, view roll numbers, contact information, and historical exam records."
                href="/students"
                icon={Users}
                color="text-violet-400"
                bg="bg-violet-500/15"
              />

              <DashboardCard
                title="Faculty Directory"
                description="Browse active teachers, view assigned departments, subjects taught, and contact details."
                href="/teachers"
                icon={BookOpen}
                color="text-pink-400"
                bg="bg-pink-500/15"
              />

              <DashboardCard
                title="School Profile & Info"
                description="Manage school name, address, school code, and contact information."
                href="/principal/school"
                icon={School}
                color="text-cyan-400"
                bg="bg-cyan-500/15"
              />

              <DashboardCard
                title="Principal Profile"
                description="Update your credentials, leadership details, and qualifications."
                href="/principal/profile"
                icon={UserCircle}
                color="text-amber-400"
                bg="bg-amber-500/15"
              />

              <DashboardCard
                title="Account Settings"
                description="Manage email, name, password security, and account preferences."
                href="/profile"
                icon={Settings}
                color="text-zinc-400"
                bg="bg-zinc-800"
              />
            </div>
          </div>
        )}

        {/* ─── TEACHER COMMAND CENTER ─── */}
        {role === "TEACHER" && (
          <div className="space-y-8">
            {/* Action Callout Banner */}
            <div className="rounded-2xl border border-indigo-500/30 bg-indigo-950/20 p-5 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-2xl bg-indigo-500/15 text-indigo-400">
                  <GraduationCap className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">
                    Class Enrollment Requests & Join Codes
                  </h3>
                  <p className="text-xs sm:text-sm text-zinc-400 mt-0.5">
                    View your classes, share 8-character student join codes, and approve student enrollment applications.
                  </p>
                </div>
              </div>
              <Link href="/teacher/classes" className="shrink-0">
                <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white">
                  Manage Classes & Requests <ArrowRight className="w-4 h-4 ml-1.5" />
                </Button>
              </Link>
            </div>

            {/* Teacher Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              <DashboardCard
                title="My Classes & Student Requests"
                description="View your assigned classes, approve pending student enrollment requests, and copy student join codes."
                href="/teacher/classes"
                icon={GraduationCap}
                color="text-indigo-400"
                bg="bg-indigo-500/15"
                badge="Classes & Requests"
                badgeVariant="default"
              />

              <DashboardCard
                title="Create New Exam"
                description="Build assessments, customize section weights, timer, negative marking, and question options."
                href="/teacher/exams/create"
                icon={Plus}
                color="text-emerald-400"
                bg="bg-emerald-500/15"
              />

              <DashboardCard
                title="Exams, Results & Marks"
                description="View exam scoreboards, grade subjective answers, inspect pass rates, and release results to students."
                href="/teacher/exams"
                icon={ClipboardList}
                color="text-blue-400"
                bg="bg-blue-500/15"
              />

              <DashboardCard
                title="Students Directory"
                description="Search students across your school, inspect roll numbers, and view complete student score records."
                href="/students"
                icon={Users}
                color="text-violet-400"
                bg="bg-violet-500/15"
              />

              <DashboardCard
                title="School Directory & Join"
                description="Access information on your current school or browse and request to join a new institution."
                href="/teacher/school"
                icon={Building2}
                color="text-amber-400"
                bg="bg-amber-500/15"
              />

              <DashboardCard
                title="Browse Available Exams"
                description="Explore all public and school-wide assessments published across the platform."
                href="/exams"
                icon={Search}
                color="text-cyan-400"
                bg="bg-cyan-500/15"
              />

              <DashboardCard
                title="Teacher Profile"
                description="Update your subjects taught, years of experience, qualifications, and profile."
                href="/teacher/profile"
                icon={UserCircle}
                color="text-pink-400"
                bg="bg-pink-500/15"
              />

              <DashboardCard
                title="Account Settings"
                description="Update personal details, password security, and account preferences."
                href="/profile"
                icon={Settings}
                color="text-zinc-400"
                bg="bg-zinc-800"
              />
            </div>
          </div>
        )}

        {/* ─── STUDENT COMMAND CENTER ─── */}
        {role === "STUDENT" && (
          <div className="space-y-8">
            {/* Student Action Banner */}
            <div className="rounded-2xl border border-sky-500/30 bg-sky-950/20 p-5 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-2xl bg-sky-500/15 text-sky-400">
                  <Award className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">
                    Exams, Results & Performance
                  </h3>
                  <p className="text-xs sm:text-sm text-zinc-400 mt-0.5">
                    View your test scores, leaderboards, answer explanations, and upcoming assessments.
                  </p>
                </div>
              </div>
              <Link href="/student/exams" className="shrink-0">
                <Button size="sm" className="bg-sky-600 hover:bg-sky-700 text-white">
                  View My Results <ArrowRight className="w-4 h-4 ml-1.5" />
                </Button>
              </Link>
            </div>

            {/* Student Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              <DashboardCard
                title="My Exams & Results"
                description="Check completed test scorecards, marks obtained, class rank, and released answer keys."
                href="/student/exams"
                icon={Award}
                color="text-sky-400"
                bg="bg-sky-500/15"
                badge="Scores & Rank"
                badgeVariant="info"
              />

              <DashboardCard
                title="Browse & Take Exams"
                description="Find scheduled assessments, enter private exam codes, and take timed tests."
                href="/exams"
                icon={Search}
                color="text-indigo-400"
                bg="bg-indigo-500/15"
              />

              <DashboardCard
                title="My Class & Teachers"
                description="View your assigned class section, teachers, class join codes, and classmates."
                href="/student/class"
                icon={GraduationCap}
                color="text-emerald-400"
                bg="bg-emerald-500/15"
              />

              <DashboardCard
                title="School Directory"
                description="Learn about your school administration, faculty, and institutional information."
                href="/student/school"
                icon={School}
                color="text-violet-400"
                bg="bg-violet-500/15"
              />

              <DashboardCard
                title="Student Profile & Join Codes"
                description="Enter class join codes, check admission status, and update guardian information."
                href="/student/profile"
                icon={UserCircle}
                color="text-amber-400"
                bg="bg-amber-500/15"
              />

              <DashboardCard
                title="Account Settings"
                description="Update your contact details, phone number, address, and password."
                href="/profile"
                icon={Settings}
                color="text-zinc-400"
                bg="bg-zinc-800"
              />
            </div>
          </div>
        )}

        {/* ─── ADMIN COMMAND CENTER ─── */}
        {role === "ADMIN" && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <DashboardCard
              title="Schools Management"
              description="Manage registered schools, verify institutions, and inspect administrative details."
              href="/schools"
              icon={School}
              color="text-amber-400"
              bg="bg-amber-500/15"
            />
            <DashboardCard
              title="Teachers Directory"
              description="Inspect faculty records, departments, and teaching assignments."
              href="/teachers"
              icon={BookOpen}
              color="text-emerald-400"
              bg="bg-emerald-500/15"
            />
            <DashboardCard
              title="Students Directory"
              description="Search all enrolled students across all registered schools."
              href="/students"
              icon={Users}
              color="text-indigo-400"
              bg="bg-indigo-500/15"
            />
            <DashboardCard
              title="All Exams"
              description="Browse and manage all tests, scoreboards, and assessments created on the platform."
              href="/exams"
              icon={ClipboardList}
              color="text-blue-400"
              bg="bg-blue-500/15"
            />
            <DashboardCard
              title="Account Settings"
              description="Manage admin credentials and system configuration."
              href="/profile"
              icon={Settings}
              color="text-zinc-400"
              bg="bg-zinc-800"
            />
          </div>
        )}
      </div>
    </div>
  );
}

interface DashboardCardProps {
  title: string;
  description: string;
  href: string;
  icon: React.ComponentType<{ className?: string; size?: number }>;
  color: string;
  bg: string;
  badge?: string;
  badgeVariant?: "default" | "secondary" | "success" | "warning" | "info" | "neutral";
}

function DashboardCard({
  title,
  description,
  href,
  icon: Icon,
  color,
  bg,
  badge,
  badgeVariant = "default",
}: DashboardCardProps) {
  return (
    <Link href={href} className="group block h-full">
      <GlassCard interactive padding="md" className="h-full flex flex-col justify-between space-y-4">
        <div>
          <div className="flex items-start justify-between mb-3">
            <div
              className={`p-3 rounded-2xl ${bg} ${color} transition-all duration-300 group-hover:scale-110`}
            >
              <Icon size={22} />
            </div>
            {badge && (
              <Badge variant={badgeVariant} className="text-[10px] px-2 py-0.5 uppercase tracking-wider font-semibold">
                {badge}
              </Badge>
            )}
          </div>
          <h3 className="text-base sm:text-lg font-bold text-[var(--text-primary)] group-hover:text-indigo-400 transition-colors">
            {title}
          </h3>
          <p className="text-xs sm:text-sm text-[var(--text-muted)] mt-1.5 leading-relaxed">
            {description}
          </p>
        </div>

        <div className="flex items-center text-xs font-semibold text-indigo-400 group-hover:text-indigo-300 pt-2">
          Open <ArrowRight className="w-3.5 h-3.5 ml-1 transition-transform group-hover:translate-x-1" />
        </div>
      </GlassCard>
    </Link>
  );
}
