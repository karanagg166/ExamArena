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
  Plus,
  School,
  Search,
  Settings,
  Sparkles,
  UserCheck,
  UserCircle,
  Users,
} from "lucide-react";

import { useSchoolStore } from "@/stores";

type User = {
  name: string;
  role: "STUDENT" | "TEACHER" | "PRINCIPAL" | "ADMIN";
  email: string;
};

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [hasStudentProfile, setHasStudentProfile] = useState<boolean>(false);
  const [loading, setLoading] = useState(true);
  const { school, hasFetched, fetchSchool } = useSchoolStore();

  useEffect(() => {
    if (!hasFetched) fetchSchool();
  }, [hasFetched, fetchSchool]);

  useEffect(() => {
    api
      .get("/api/v1/auth/me")
      .then((r) => {
        setUser(r.data);
        if (r.data.role === "STUDENT") {
          api
            .get("/api/v1/students/me")
            .then(() => setHasStudentProfile(true))
            .catch(() => setHasStudentProfile(false));
        }
      })
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
                  "Review teacher & student join requests, oversee school classes and student rosters, and inspect exam performance."}
                {role === "TEACHER" &&
                  "Review student class enrollment requests, manage join codes, create exams, and track student scores."}
                {role === "STUDENT" &&
                  "Join classes with join codes, take scheduled assessments, and view your graded results and marks."}
                {role === "ADMIN" &&
                  "Platform administration, manage registered schools, teachers, students, and system exams."}
              </p>
            </div>

            {/* Quick Action Ribbon */}
            <div className="flex flex-wrap items-center gap-2 shrink-0">
              {role === "PRINCIPAL" && (
                <>
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
                  <Link href="/teacher/exams/create">
                    <Button size="sm" variant="secondary" className="text-xs">
                      <Plus className="w-3.5 h-3.5 mr-1" /> Create Exam
                    </Button>
                  </Link>
                </>
              )}

              {role === "TEACHER" && (
                <>
                  <Link href="/teacher/requests?tab=students">
                    <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm text-xs">
                      <UserCheck className="w-3.5 h-3.5 mr-1" /> Student Requests
                    </Button>
                  </Link>
                  {!school ? (
                    <Link href="/teacher/school/join">
                      <Button size="sm" className="bg-amber-500 hover:bg-amber-600 text-white shadow-sm text-xs">
                        <School className="w-3.5 h-3.5 mr-1" /> Join School
                      </Button>
                    </Link>
                  ) : (
                    <Link href="/teacher/school">
                      <Button size="sm" variant="outline" className="border-indigo-500/40 text-indigo-300 hover:bg-indigo-950/30 text-xs">
                        <Building2 className="w-3.5 h-3.5 mr-1 text-indigo-400" /> {school.name}
                      </Button>
                    </Link>
                  )}
                  <Link href="/teacher/exams/create">
                    <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm text-xs">
                      <Plus className="w-3.5 h-3.5 mr-1" /> Create Exam
                    </Button>
                  </Link>
                </>
              )}

              {role === "STUDENT" && (
                <>
                  {!hasStudentProfile && (
                    <Link href="/student/profile">
                      <Button size="sm" className="bg-amber-500 hover:bg-amber-600 text-white shadow-sm text-xs">
                        <GraduationCap className="w-3.5 h-3.5 mr-1" /> Join Class Code
                      </Button>
                    </Link>
                  )}
                  <Link href="/exams">
                    <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm text-xs">
                      <Sparkles className="w-3.5 h-3.5 mr-1" /> Take Exam
                    </Button>
                  </Link>
                  <Link href="/student/exams">
                    <Button size="sm" variant="secondary" className="text-xs">
                      <Award className="w-3.5 h-3.5 mr-1" /> View Results
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
            {/* Direct Request Hub Callouts */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-5 rounded-2xl border border-amber-500/30 bg-amber-950/20 flex flex-col justify-between space-y-3">
                <div className="flex items-start gap-3">
                  <div className="p-2.5 rounded-xl bg-amber-500/15 text-amber-400">
                    <UserCheck className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white">Teacher Join Requests</h4>
                    <p className="text-xs text-zinc-400 mt-0.5">Faculty applications seeking to join your school.</p>
                  </div>
                </div>
                <Link href="/principal/teacher-requests?tab=faculty">
                  <Button size="sm" className="w-full bg-amber-500 hover:bg-amber-600 text-white text-xs">
                    Review Teacher Requests <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Button>
                </Link>
              </div>

              <div className="p-5 rounded-2xl border border-indigo-500/30 bg-indigo-950/20 flex flex-col justify-between space-y-3">
                <div className="flex items-start gap-3">
                  <div className="p-2.5 rounded-xl bg-indigo-500/15 text-indigo-400">
                    <BookOpen className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white">Class Teaching Requests</h4>
                    <p className="text-xs text-zinc-400 mt-0.5">Teachers requesting to teach specific class sections.</p>
                  </div>
                </div>
                <Link href="/principal/teacher-requests?tab=teaching">
                  <Button size="sm" className="w-full bg-indigo-600 hover:bg-indigo-700 text-white text-xs">
                    Review Teaching Requests <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Button>
                </Link>
              </div>

              <div className="p-5 rounded-2xl border border-emerald-500/30 bg-emerald-950/20 flex flex-col justify-between space-y-3">
                <div className="flex items-start gap-3">
                  <div className="p-2.5 rounded-xl bg-emerald-500/15 text-emerald-400">
                    <GraduationCap className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white">Student Admissions</h4>
                    <p className="text-xs text-zinc-400 mt-0.5">Students enrolling with class join codes.</p>
                  </div>
                </div>
                <Link href="/principal/teacher-requests?tab=students">
                  <Button size="sm" className="w-full bg-emerald-600 hover:bg-emerald-700 text-white text-xs">
                    Review Student Requests <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Button>
                </Link>
              </div>
            </div>

            {/* Principal Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              <DashboardCard
                title="School Requests & Approvals"
                description="Review incoming faculty join requests, teaching class assignments, and student enrollment approvals in one central hub."
                href="/principal/teacher-requests"
                icon={UserCheck}
                color="text-amber-400"
                bg="bg-amber-500/15"
                badge="Approvals Hub"
                badgeVariant="warning"
              />

              <DashboardCard
                title="Classes, Roster & Join Codes"
                description="Manage all classes, generate 8-character student join codes, assign faculty, and inspect class exam scorecards."
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
            {/* Direct Request Hub Callouts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-5 rounded-2xl border border-emerald-500/30 bg-emerald-950/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="p-2.5 rounded-xl bg-emerald-500/15 text-emerald-400">
                    <GraduationCap className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white">Student Class Join Requests</h4>
                    <p className="text-xs text-zinc-400 mt-0.5">Approve incoming students who enrolled using your class join code.</p>
                  </div>
                </div>
                <Link href="/teacher/requests?tab=students" className="shrink-0">
                  <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs">
                    Accept Student Requests <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Button>
                </Link>
              </div>

              {!school ? (
                <div className="p-5 rounded-2xl border border-amber-500/30 bg-amber-950/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <div className="p-2.5 rounded-xl bg-amber-500/15 text-amber-400">
                      <School className="h-5 w-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white">School Join Requests & Status</h4>
                      <p className="text-xs text-zinc-400 mt-0.5">Browse schools or check your faculty application approval status.</p>
                    </div>
                  </div>
                  <Link href="/teacher/school/join" className="shrink-0">
                    <Button size="sm" className="bg-amber-500 hover:bg-amber-600 text-white text-xs">
                      Join School / Status <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="p-5 rounded-2xl border border-indigo-500/30 bg-indigo-950/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <div className="p-2.5 rounded-xl bg-indigo-500/15 text-indigo-400">
                      <Building2 className="h-5 w-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white">Enrolled in {school.name}</h4>
                      <p className="text-xs text-zinc-400 mt-0.5">School Code: {school.schoolCode} • Manage assigned classes and roster.</p>
                    </div>
                  </div>
                  <Link href="/teacher/school" className="shrink-0">
                    <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs">
                      School Profile <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </Link>
                </div>
              )}
            </div>

            {/* Teacher Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              <DashboardCard
                title="Student Requests & Approvals"
                description="View and accept incoming student enrollment applications and manage your school join status in one place."
                href="/teacher/requests"
                icon={UserCheck}
                color="text-emerald-400"
                bg="bg-emerald-500/15"
                badge="Requests Center"
                badgeVariant="success"
              />

              <DashboardCard
                title="My Classes & Join Codes"
                description="View your assigned classes, copy 8-character student enrollment codes, and manage class student rosters."
                href="/teacher/classes"
                icon={GraduationCap}
                color="text-indigo-400"
                bg="bg-indigo-500/15"
                badge="Classes & Roster"
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

              {!school ? (
                <DashboardCard
                  title="Join a School"
                  description="Browse available institutions and submit direct faculty join applications."
                  href="/teacher/school/join"
                  icon={School}
                  color="text-amber-400"
                  bg="bg-amber-500/15"
                />
              ) : (
                <DashboardCard
                  title="School Directory"
                  description="Access information on your current school administration and faculty members."
                  href="/teacher/school"
                  icon={Building2}
                  color="text-cyan-400"
                  bg="bg-cyan-500/15"
                />
              )}

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
            {/* Student Action Banners */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {!hasStudentProfile ? (
                <div className="p-5 rounded-2xl border border-amber-500/30 bg-amber-950/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <div className="p-2.5 rounded-xl bg-amber-500/15 text-amber-400">
                      <GraduationCap className="h-5 w-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white">Join a Class with Code</h4>
                      <p className="text-xs text-zinc-400 mt-0.5">Enter the 8-character class join code given by your teacher.</p>
                    </div>
                  </div>
                  <Link href="/student/profile" className="shrink-0">
                    <Button size="sm" className="bg-amber-500 hover:bg-amber-600 text-white text-xs">
                      Enter Join Code <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="p-5 rounded-2xl border border-emerald-500/30 bg-emerald-950/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <div className="p-2.5 rounded-xl bg-emerald-500/15 text-emerald-400">
                      <GraduationCap className="h-5 w-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white">My Enrolled Class</h4>
                      <p className="text-xs text-zinc-400 mt-0.5">View your class section details, assigned teachers, and peers.</p>
                    </div>
                  </div>
                  <Link href="/student/class" className="shrink-0">
                    <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs">
                      View My Class <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </Link>
                </div>
              )}

              <div className="p-5 rounded-2xl border border-sky-500/30 bg-sky-950/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="p-2.5 rounded-xl bg-sky-500/15 text-sky-400">
                    <Award className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white">Exams & Scorecards</h4>
                    <p className="text-xs text-zinc-400 mt-0.5">View your completed test results, marks, percentage, and rank.</p>
                  </div>
                </div>
                <Link href="/student/exams" className="shrink-0">
                  <Button size="sm" className="bg-sky-600 hover:bg-sky-700 text-white text-xs">
                    View My Marks <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Button>
                </Link>
              </div>
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

              {!hasStudentProfile ? (
                <DashboardCard
                  title="Class Enrollment & Join Codes"
                  description="Enter class join codes, check admission status, and update guardian information."
                  href="/student/profile"
                  icon={UserCircle}
                  color="text-amber-400"
                  bg="bg-amber-500/15"
                  badge="Join Code"
                  badgeVariant="warning"
                />
              ) : (
                <DashboardCard
                  title="My Profile & Roll No"
                  description="View your active student profile, assigned roll number, and personal details."
                  href="/student/profile"
                  icon={UserCircle}
                  color="text-amber-400"
                  bg="bg-amber-500/15"
                  badge="Profile"
                  badgeVariant="default"
                />
              )}

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
                title="Classmates Directory"
                description="Explore and connect with peers and classmates enrolled across your school."
                href="/students"
                icon={Users}
                color="text-pink-400"
                bg="bg-pink-500/15"
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
