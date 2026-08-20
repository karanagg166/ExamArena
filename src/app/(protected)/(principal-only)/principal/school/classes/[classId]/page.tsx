"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/loading";
import { Button } from "@/components/ui/button";
import { useAuthStore, useSchoolClassStore } from "@/stores";
import { api } from "@/lib/axios";
import { formatDateIST } from "@/lib/date";
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Copy,
  LayoutDashboard,
  Trash2,
  TrendingUp,
  Users,
} from "lucide-react";
import { toast } from "sonner";

interface ClassExamResultData {
  classId: string;
  className: string;
  totalStudents: number;
  totalSubmissions: number;
  classAveragePercentage: number;
  examsSummary: {
    examId: string;
    examTitle: string;
    subject?: string;
    maxMarks: number;
    attemptsCount: number;
    averageScore: number;
    averagePercentage: number;
    highestScore: number;
    isResultsReleased: boolean;
  }[];
  students: {
    studentId: string;
    studentName: string;
    rollNo: string | null;
    email: string;
    totalAttempts: number;
    attempts: {
      attemptId: string;
      examId: string;
      examTitle: string;
      marksObtained: number;
      maxMarks: number;
      percentage: number;
      status: string;
      isResultsReleased: boolean;
    }[];
  }[];
}

export default function ClassPage() {
  const { classId } = useParams<{ classId: string }>();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const { classes, loading, error, fetchClass, deleteClass } = useSchoolClassStore();

  const [activeTab, setActiveTab] = useState<"overview" | "results">("overview");
  const [resultsData, setResultsData] = useState<ClassExamResultData | null>(null);
  const [loadingResults, setLoadingResults] = useState(false);

  useEffect(() => {
    if (user && user.role !== "PRINCIPAL" && user.role !== "ADMIN") {
      router.replace(`/teacher/classes/${classId}`);
    }
  }, [user, classId, router]);

  const schoolClass = classes.find((c) => c.id === classId);
  useEffect(() => {
    if (classId && !schoolClass) {
      fetchClass(classId);
    }
  }, [classId, fetchClass, schoolClass]);

  useEffect(() => {
    let ignore = false;
    if (activeTab === "results" && classId && !resultsData) {
      const load = async () => {
        setLoadingResults(true);
        try {
          const res = await api.get<ClassExamResultData>(`/api/v1/classes/${classId}/results`);
          if (!ignore) {
            setResultsData(res.data);
          }
        } catch {
          // ignore or empty
        } finally {
          if (!ignore) {
            setLoadingResults(false);
          }
        }
      };
      load();
    }
    return () => {
      ignore = true;
    };
  }, [activeTab, classId, resultsData]);

  const handleDelete = async () => {
    if (!schoolClass) return;
    if (window.confirm(`Are you sure you want to delete class '${schoolClass.name}'?`)) {
      const success = await deleteClass(schoolClass.id);
      if (success) {
        toast.success(`Class '${schoolClass.name}' deleted successfully`);
        router.push("/principal/school/classes");
      } else {
        toast.error("Failed to delete class");
      }
    }
  };

  const copyJoinCode = () => {
    if (schoolClass?.joinCode) {
      navigator.clipboard.writeText(schoolClass.joinCode);
      toast.success(`Copied join code: ${schoolClass.joinCode}`);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-8 w-8 border-4" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-shell text-white">
        <Card className="max-w-2xl border-red-500/30">
          <CardHeader>
            <CardTitle className="text-red-300">Unable to load class</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-red-200">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!schoolClass) return null;

  return (
    <div className="page-shell text-white space-y-6 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <Button
          variant="ghost"
          className="text-zinc-400 hover:text-white pl-0"
          onClick={() => router.push("/principal/school/classes")}
        >
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Classes
        </Button>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push(`/principal/school/classes/${classId}/students`)}
          >
            <Users className="w-4 h-4 mr-2" /> View Students Roster
          </Button>
          <Button variant="destructive" size="sm" onClick={handleDelete}>
            <Trash2 className="w-4 h-4 mr-2" /> Delete Class
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-zinc-800 gap-6">
        <button
          type="button"
          onClick={() => setActiveTab("overview")}
          className={`flex items-center gap-2 pb-3 font-semibold text-sm transition-colors border-b-2 ${
            activeTab === "overview"
              ? "border-indigo-500 text-indigo-400"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <LayoutDashboard className="w-4 h-4" /> Class Overview
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("results")}
          className={`flex items-center gap-2 pb-3 font-semibold text-sm transition-colors border-b-2 ${
            activeTab === "results"
              ? "border-indigo-500 text-indigo-400"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <TrendingUp className="w-4 h-4" /> Exam Results & Performance
        </button>
      </div>

      {activeTab === "overview" ? (
        <Card className="space-y-6">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-2xl">{schoolClass.name}</CardTitle>
              {schoolClass.schoolName && (
                <p className="text-sm text-zinc-400 mt-1">
                  {schoolClass.schoolName}
                </p>
              )}
            </div>
            <span className="text-xs bg-indigo-50 text-indigo-700 font-medium px-3 py-1 rounded-full border border-indigo-100">
              {schoolClass.teachers?.length ?? 0} Teacher{schoolClass.teachers?.length !== 1 ? "s" : ""} Assigned
            </span>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Join Code Banner */}
            {schoolClass.joinCode && (
              <div className="rounded-xl border border-indigo-400/25 bg-indigo-500/5 p-4">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-300">
                      Student Enrollment Code
                    </p>
                    <p className="mt-1 font-mono text-2xl font-bold tracking-[0.2em] text-white">
                      {schoolClass.joinCode}
                    </p>
                    <p className="mt-1 text-xs text-zinc-400">
                      Share this code with students to let them request to join this class.
                    </p>
                  </div>
                  <Button variant="outline" size="sm" onClick={copyJoinCode}>
                    <Copy className="mr-2 h-4 w-4" /> Copy Code
                  </Button>
                </div>
              </div>
            )}

            {/* Basic Info */}
            <div className="grid gap-2 text-sm text-zinc-300 sm:grid-cols-2">
              <p>
                <span className="text-zinc-500">Class Name:</span> {schoolClass.name}
              </p>
              <p>
                <span className="text-zinc-500">School:</span>{" "}
                {schoolClass.schoolName || "My School"}
              </p>
              <p>
                <span className="text-zinc-500">Created:</span>{" "}
                {formatDateIST(schoolClass.createdAt)}
              </p>
              <p>
                <span className="text-zinc-500">Updated:</span>{" "}
                {formatDateIST(schoolClass.updatedAt)}
              </p>
            </div>

            {/* Teachers */}
            {schoolClass.teachers && schoolClass.teachers.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wide">
                  Assigned Teachers ({schoolClass.teachers.length})
                </h3>
                <div className="grid gap-2 sm:grid-cols-2">
                  {schoolClass.teachers.map((teacher) => (
                    <div
                      key={teacher.id}
                      className="rounded-lg border border-zinc-700 bg-zinc-800/50 px-4 py-3 text-sm"
                    >
                      <p className="font-medium text-zinc-200">{teacher.name}</p>
                      <p className="text-zinc-500 text-xs mt-0.5">
                        {teacher.department} {teacher.subjects?.length ? `• ${teacher.subjects.join(", ")}` : ""}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* No teachers fallback */}
            {(!schoolClass.teachers || schoolClass.teachers.length === 0) && (
              <p className="text-sm text-zinc-500">
                No teachers assigned to this class yet.
              </p>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {loadingResults ? (
            <GlassCard padding="lg" className="text-center p-12 text-zinc-400">
              <div className="w-8 h-8 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin mx-auto mb-3" />
              Loading exam results for {schoolClass.name}...
            </GlassCard>
          ) : resultsData ? (
            <>
              {/* Stats Row */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <GlassCard padding="md" className="space-y-1">
                  <p className="text-xs text-zinc-400 uppercase font-semibold flex items-center gap-1.5">
                    <Users className="w-4 h-4 text-indigo-400" /> Total Students
                  </p>
                  <p className="text-2xl font-bold text-white">
                    {resultsData.totalStudents}
                  </p>
                </GlassCard>

                <GlassCard padding="md" className="space-y-1">
                  <p className="text-xs text-zinc-400 uppercase font-semibold flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Total Submissions
                  </p>
                  <p className="text-2xl font-bold text-emerald-400">
                    {resultsData.totalSubmissions}
                  </p>
                </GlassCard>

                <GlassCard padding="md" className="space-y-1">
                  <p className="text-xs text-zinc-400 uppercase font-semibold flex items-center gap-1.5">
                    <TrendingUp className="w-4 h-4 text-amber-400" /> Class Average
                  </p>
                  <p className="text-2xl font-bold text-amber-400">
                    {resultsData.classAveragePercentage}%
                  </p>
                </GlassCard>
              </div>

              {/* Assessments Summary */}
              {resultsData.examsSummary.length > 0 && (
                <GlassCard padding="lg" className="space-y-4">
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <BookOpen className="w-5 h-5 text-indigo-400" />
                    Class Assessments ({resultsData.examsSummary.length})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {resultsData.examsSummary.map((exam) => (
                      <div
                        key={exam.examId}
                        className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/60 space-y-3"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <h4 className="font-bold text-white text-base">
                              {exam.examTitle}
                            </h4>
                            <p className="text-xs text-zinc-400">
                              {exam.subject} • Max Marks: {exam.maxMarks}
                            </p>
                          </div>
                          <Badge
                            variant={exam.isResultsReleased ? "success" : "neutral"}
                            className="text-[10px]"
                          >
                            {exam.isResultsReleased ? "Released" : "Pending"}
                          </Badge>
                        </div>

                        <div className="grid grid-cols-3 gap-2 text-xs pt-2 border-t border-zinc-800 text-zinc-300">
                          <div>
                            <span className="text-zinc-500 block">Attempts:</span>
                            <strong>{exam.attemptsCount}</strong>
                          </div>
                          <div>
                            <span className="text-zinc-500 block">Class Avg:</span>
                            <strong className="text-amber-300">
                              {exam.averageScore} ({exam.averagePercentage}%)
                            </strong>
                          </div>
                          <div>
                            <span className="text-zinc-500 block">Highest:</span>
                            <strong className="text-emerald-400">{exam.highestScore}</strong>
                          </div>
                        </div>

                        <Link href={`/teacher/exams/${exam.examId}/results`}>
                          <Button size="sm" variant="outline" className="w-full text-xs mt-2">
                            View Exam Scoreboard
                            <ChevronRight className="w-3.5 h-3.5 ml-1" />
                          </Button>
                        </Link>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              )}

              {/* Student Scores Roster */}
              <GlassCard padding="lg" className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Users className="w-5 h-5 text-indigo-400" />
                    Student Roster & Scores
                  </h3>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => router.push(`/principal/school/classes/${classId}/students`)}
                  >
                    Manage Full Roster →
                  </Button>
                </div>

                {resultsData.students.length === 0 ? (
                  <p className="text-sm text-zinc-500">No students enrolled in this class.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-zinc-300">
                      <thead className="text-xs uppercase bg-zinc-800/80 text-zinc-400 border-b border-zinc-700">
                        <tr>
                          <th className="px-4 py-3">Roll No</th>
                          <th className="px-4 py-3">Student Name</th>
                          <th className="px-4 py-3">Email</th>
                          <th className="px-4 py-3">Completed Tests</th>
                          <th className="px-4 py-3">Performance</th>
                          <th className="px-4 py-3 text-right">Student Record</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-800">
                        {resultsData.students.map((student) => (
                          <tr key={student.studentId} className="hover:bg-zinc-800/40">
                            <td className="px-4 py-3 font-mono font-bold text-indigo-400">
                              {student.rollNo ?? "--"}
                            </td>
                            <td className="px-4 py-3 font-medium text-white">
                              {student.studentName}
                            </td>
                            <td className="px-4 py-3 text-xs text-zinc-400">
                              {student.email}
                            </td>
                            <td className="px-4 py-3">
                              <Badge variant="neutral" className="text-xs">
                                {student.totalAttempts} Submissions
                              </Badge>
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex flex-wrap gap-1.5">
                                {student.attempts.length === 0 ? (
                                  <span className="text-xs text-zinc-500 italic">No exams yet</span>
                                ) : (
                                  student.attempts.map((att) => (
                                    <span
                                      key={att.attemptId}
                                      className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded bg-zinc-800 border border-zinc-700"
                                      title={`${att.examTitle}: ${att.marksObtained}/${att.maxMarks} (${att.percentage}%)`}
                                    >
                                      <span className="truncate max-w-[80px] text-zinc-300">
                                        {att.examTitle}
                                      </span>
                                      <strong className={att.percentage >= 60 ? "text-emerald-400" : "text-amber-400"}>
                                        {att.percentage}%
                                      </strong>
                                    </span>
                                  ))
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-3 text-right">
                              <Link href={`/students/${student.studentId}`}>
                                <Button variant="ghost" size="sm" className="text-indigo-400 hover:text-indigo-300 text-xs">
                                  View Record <ChevronRight className="w-3.5 h-3.5 ml-1" />
                                </Button>
                              </Link>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </GlassCard>
            </>
          ) : (
            <GlassCard padding="lg" className="text-center p-12 text-zinc-400">
              No exam records found for this class yet.
            </GlassCard>
          )}
        </div>
      )}
    </div>
  );
}
