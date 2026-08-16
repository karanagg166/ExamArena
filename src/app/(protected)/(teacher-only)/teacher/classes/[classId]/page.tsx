"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/loading";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { GlassCard } from "@/components/ui/glass-card";
import { useSchoolClassStore } from "@/stores";
import { api } from "@/lib/axios";
import {
  ArrowLeft,
  Copy,
  ListChecks,
  Award,
  BookOpen,
  Users,
  CheckCircle2,
  ChevronRight,
  TrendingUp,
  UserPlus,
  Check,
  X,
} from "lucide-react";
import { toast } from "sonner";
import Link from "next/link";
import { getErrorMessage } from "@/lib/error";

interface ClassExamResultData {
  classId: string;
  totalStudents: number;
  totalSubmissions: number;
  classAveragePercentage: number;
  students: {
    studentId: string;
    userId: string;
    studentName: string;
    email: string;
    rollNo: number | null;
    totalAttempts: number;
    attempts: {
      attemptId: string;
      examId: string;
      examTitle: string;
      examCode?: string;
      subject?: string;
      marksObtained: number;
      maxMarks: number;
      percentage: number;
      status: string;
      isResultsReleased: boolean;
      submittedAt: string;
    }[];
  }[];
  examsSummary: {
    examId: string;
    examTitle: string;
    examCode?: string;
    subject?: string;
    maxMarks: number;
    attemptsCount: number;
    averageScore: number;
    averagePercentage: number;
    highestScore: number;
    isResultsReleased: boolean;
  }[];
}

export default function ClassPage() {
  const { classId } = useParams<{ classId: string }>();
  const router = useRouter();
  const { classes, loading, error, fetchClass } = useSchoolClassStore();

  const [activeTab, setActiveTab] = useState<"overview" | "results">("overview");
  const [resultsData, setResultsData] = useState<ClassExamResultData | null>(null);
  const [loadingResults, setLoadingResults] = useState(false);
  const [isAssigned, setIsAssigned] = useState(false);

  // Request to teach modal
  const [requestModalOpen, setRequestModalOpen] = useState(false);
  const [selectedSubject, setSelectedSubject] = useState("MATHS");
  const [requesting, setRequesting] = useState(false);
  const [requestSuccess, setRequestSuccess] = useState<string | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);

  const schoolClass = classes.find((c) => c.id === classId);
  useEffect(() => {
    if (classId && !schoolClass) {
      fetchClass(classId);
    }
  }, [classId, fetchClass, schoolClass]);

  useEffect(() => {
    api
      .get("/api/v1/teachers/me")
      .then((res) => {
        const teaches = res.data?.teaches || [];
        const assigned = teaches.some((t: { classId: string }) => t.classId === classId);
        setIsAssigned(assigned);
      })
      .catch(() => {});
  }, [classId]);

  useEffect(() => {
    if (!classId) return;
    let isMounted = true;
    const loadResults = async () => {
      try {
        const res = await api.get(`/api/v1/classes/${classId}/results`);
        if (isMounted) {
          setResultsData(res.data);
        }
      } catch {
        // results unavailable or no submissions yet
      } finally {
        if (isMounted) {
          setLoadingResults(false);
        }
      }
    };

    void loadResults();
    return () => {
      isMounted = false;
    };
  }, [classId]);

  const handleSendRequest = async () => {
    if (!classId) return;
    setRequesting(true);
    setRequestError(null);
    setRequestSuccess(null);
    try {
      await api.post("/api/v1/teacher-requests", {
        classId: classId,
        subject: selectedSubject || null,
      });
      setRequestSuccess("Your request to teach this class has been sent to the Principal for approval!");
      setTimeout(() => {
        setRequestModalOpen(false);
        setRequestSuccess(null);
      }, 2500);
    } catch (err: unknown) {
      setRequestError(getErrorMessage(err));
    } finally {
      setRequesting(false);
    }
  };

  const copyJoinCode = async () => {
    if (!schoolClass) return;
    try {
      await navigator.clipboard.writeText(schoolClass.joinCode);
      toast.success("Join code copied to clipboard");
    } catch {
      toast.error("Unable to copy the join code");
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
    <div className="page-shell text-white">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <Button
            variant="ghost"
            className="text-zinc-400 hover:text-white"
            onClick={() => router.back()}
          >
            <ArrowLeft className="w-4 h-4 mr-2" /> Back
          </Button>

          {/* Navigation Tabs */}
          <div className="inline-flex rounded-xl border border-[var(--border-default)] p-1 bg-[var(--surface-1)]">
            <Button
              type="button"
              size="sm"
              variant={activeTab === "overview" ? "secondary" : "ghost"}
              onClick={() => setActiveTab("overview")}
            >
              Class Overview
            </Button>
            <Button
              type="button"
              size="sm"
              variant={activeTab === "results" ? "secondary" : "ghost"}
              onClick={() => setActiveTab("results")}
            >
              <Award className="w-4 h-4 mr-1.5 text-amber-400" />
              Exam Results & Performance
            </Button>
          </div>
        </div>

        {activeTab === "overview" ? (
          <Card className="space-y-6">
            {/* Header */}
            <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <CardTitle className="text-2xl">{schoolClass.name}</CardTitle>
                  {isAssigned && (
                    <Badge variant="success" className="text-[10px] uppercase font-bold tracking-wider">
                      You Teach This Class
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-zinc-400 mt-1">
                  {schoolClass.schoolName || "School Class"} • Year: {schoolClass.year} • Section: {schoolClass.section}
                </p>
              </div>
              {!isAssigned && (
                <Button
                  size="sm"
                  onClick={() => setRequestModalOpen(true)}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs"
                >
                  <UserPlus className="w-3.5 h-3.5 mr-1" /> Request to Teach Class
                </Button>
              )}
            </CardHeader>

            <CardContent className="space-y-6">
              <div className="rounded-xl border border-indigo-400/25 bg-indigo-500/5 p-4">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-300">
                      Student enrollment code
                    </p>
                    <p className="mt-1 font-mono text-2xl font-bold tracking-[0.2em] text-white">
                      {schoolClass.joinCode}
                    </p>
                    <p className="mt-1 text-sm text-zinc-400">
                      Share this code with students; requests require your approval.
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button variant="outline" size="sm" onClick={copyJoinCode}>
                      <Copy className="mr-2 h-4 w-4" /> Copy
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => router.push(`/teacher/classes/${classId}/students`)}
                    >
                      <Users className="mr-2 h-4 w-4" /> Students
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => router.push(`/teacher/classes/${classId}/requests`)}
                    >
                      <ListChecks className="mr-2 h-4 w-4" /> Requests
                    </Button>
                  </div>
                </div>
              </div>

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
                  {new Date(schoolClass.createdAt).toLocaleDateString()}
                </p>
                <p>
                  <span className="text-zinc-500">Updated:</span>{" "}
                  {new Date(schoolClass.updatedAt).toLocaleDateString()}
                </p>
              </div>

              {/* Teachers */}
              {schoolClass.teachers && schoolClass.teachers.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wide">
                    Teachers ({schoolClass.teachers.length})
                  </h3>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {schoolClass.teachers.map((teacher) => (
                      <div
                        key={teacher.id}
                        className="rounded-lg border border-zinc-700 bg-zinc-800/50 px-4 py-3 text-sm"
                      >
                        <p className="font-medium text-zinc-200">{teacher.name}</p>
                        <p className="text-zinc-500 text-xs mt-0.5">
                          {teacher.department}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* No teachers fallback */}
              {(!schoolClass.teachers || schoolClass.teachers.length === 0) && (
                <p className="text-sm text-zinc-500">
                  No teachers assigned to this class.
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

                {/* Exam Breakdown */}
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
                              View Full Exam Scoreboard
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
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Users className="w-5 h-5 text-indigo-400" />
                    Student Roster & Scores
                  </h3>

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

      {/* Modal for Requesting to Teach this Class */}
      {requestModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-zinc-800 bg-zinc-900 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <UserPlus size={18} className="text-indigo-400" />
                Request to Teach {schoolClass.name}
              </h3>
              <button
                onClick={() => setRequestModalOpen(false)}
                className="text-zinc-400 hover:text-white"
              >
                <X size={18} />
              </button>
            </div>

            <p className="text-xs text-zinc-400">
              Select your primary subject for this class. Your teaching application will be sent to the Principal for review and approval.
            </p>

            {requestSuccess ? (
              <div className="rounded-xl bg-emerald-950/50 border border-emerald-500/40 p-4 text-emerald-300 text-sm flex items-center gap-3">
                <Check className="h-5 w-5 text-emerald-400 shrink-0" />
                {requestSuccess}
              </div>
            ) : (
              <div className="space-y-4 pt-2">
                {requestError && (
                  <div className="rounded-xl bg-red-950/50 border border-red-500/40 p-3 text-red-300 text-xs">
                    {requestError}
                  </div>
                )}

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-zinc-300">Teaching Subject</label>
                  <select
                    value={selectedSubject}
                    onChange={(e) => setSelectedSubject(e.target.value)}
                    className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="MATHS">Mathematics</option>
                    <option value="SCIENCE">Science (Physics / Chemistry / Biology)</option>
                    <option value="LITERATURE">English / Literature</option>
                    <option value="HISTORY">History & Social Studies</option>
                    <option value="ART">Art & Design</option>
                    <option value="MUSIC">Music</option>
                    <option value="PHYSICAL_EDUCATION">Physical Education</option>
                  </select>
                </div>

                <div className="flex items-center justify-end gap-3 pt-3">
                  <Button
                    variant="ghost"
                    onClick={() => setRequestModalOpen(false)}
                    disabled={requesting}
                    className="text-zinc-400"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSendRequest}
                    disabled={requesting}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white"
                  >
                    {requesting ? "Sending..." : "Submit Request"}
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

