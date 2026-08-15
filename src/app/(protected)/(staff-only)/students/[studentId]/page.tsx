"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/axios";
import { Spinner } from "@/components/ui/loading";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ArrowLeft,
  Mail,
  Phone,
  MapPin,
  Calendar,
  Hash,
  Users,
  User,
  ClipboardList,
  MessageSquare,
  FileText,
} from "lucide-react";

/** Shape returned by GET /api/v1/students/:id */
type StudentDetailResponse = {
  id: string;
  userId: string;
  rollNo: string;
  parentName?: string | null;
  parentEmail?: string | null;
  fatherName?: string | null;
  fatherEmail?: string | null;
  fatherPhoneNo?: string | null;
  motherName?: string | null;
  motherEmail?: string | null;
  motherPhoneNo?: string | null;
  guardianName?: string | null;
  guardianRelation?: string | null;
  guardianEmail?: string | null;
  guardianPhoneNo?: string | null;
  dateOfAdmission: string;
  schoolId: string;
  schoolName?: string | null;
  classId: string;
  className?: string | null;
  user: {
    id: string;
    name: string;
    email: string;
    phoneNo: string;
    city: string;
    state: string;
    country: string;
    pincode: string;
  };
};

type StudentExamHistory = {
  id: string;
  examId: string;
  examTitle: string;
  examCode: string;
  subject?: string | null;
  examType: string;
  scheduledAt: string;
  submittedAt?: string | null;
  status: string;
  marksObtained: number;
  maxMarks: number;
  percentage: number;
  isResultsReleased: boolean;
};

const fmt = (ds: string | null | undefined) => {
  if (!ds) return "—";
  try {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "2-digit",
      year: "numeric",
    }).format(new Date(ds));
  } catch {
    return "—";
  }
};

export default function StudentDetailPage() {
  const { studentId } = useParams<{ studentId: string }>();
  const router = useRouter();

  const [activeTab, setActiveTab] = useState<"profile" | "exams" | "chat">("profile");
  const [student, setStudent] = useState<StudentDetailResponse | null>(null);
  const [examHistory, setExamHistory] = useState<StudentExamHistory[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingExams, setLoadingExams] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStudent = async () => {
      setLoading(true);
      setError(null);
      try {
        const { data } = await api.get<StudentDetailResponse>(
          `/api/v1/students/${studentId}`,
        );
        setStudent(data);
      } catch (err: unknown) {
        const detail =
          (err as { response?: { data?: { detail?: string } } })?.response
            ?.data?.detail;
        setError(detail ?? (err as Error)?.message ?? "Something went wrong");
      } finally {
        setLoading(false);
      }
    };

    if (studentId) fetchStudent();
  }, [studentId]);

  useEffect(() => {
    const fetchExams = async () => {
      if (activeTab !== "exams" && activeTab !== "profile") return;
      setLoadingExams(true);
      try {
        const { data } = await api.get<StudentExamHistory[]>(
          `/api/v1/students/${studentId}/exams`,
        );
        setExamHistory(data);
      } catch {
        // Exam history can fail silently if not yet available
      } finally {
        setLoadingExams(false);
      }
    };

    if (studentId) fetchExams();
  }, [studentId, activeTab]);

  if (loading) {
    return (
      <div className="flex min-h-[80vh] items-center justify-center rounded-xl m-4 bg-gray-50/50 dark:bg-slate-900/50">
        <Spinner className="h-10 w-10 text-indigo-600 border-4" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 min-h-[80vh] flex items-center justify-center">
        <Card className="max-w-md w-full border-red-500/30 shadow-red-500/10 shadow-xl">
          <CardContent className="space-y-4 pt-6">
            <h2 className="text-red-500 font-bold flex items-center gap-2">
              <span>⚠️</span> Unable to load profile
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-300">{error}</p>
            <Button
              variant="outline"
              onClick={() => router.back()}
              className="w-full"
            >
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!student) return null;

  const { user } = student;
  const totalExamsAttempted = examHistory.length;
  const gradedExams = examHistory.filter((e) => e.status === "GRADED" || e.status === "SUBMITTED");
  const avgPercentage =
    gradedExams.length > 0
      ? Math.round(
          gradedExams.reduce((acc, curr) => acc + curr.percentage, 0) /
            gradedExams.length,
        )
      : 0;

  return (
    <div className="p-4 md:p-8 min-h-screen bg-transparent">
      {/* Back button */}
      <div className="max-w-5xl mx-auto mb-6 flex items-center justify-between">
        <Button
          variant="ghost"
          onClick={() => router.back()}
          className="text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 flex items-center gap-2 -ml-4"
        >
          <ArrowLeft size={16} />
          Back to Students
        </Button>
        <Link href={`/chat?userId=${user.id}`}>
          <Button variant="primary" size="sm" className="flex items-center gap-2 shadow-sm">
            <MessageSquare size={16} />
            Direct Chat
          </Button>
        </Link>
      </div>

      <div className="w-full max-w-5xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
        {/* Hero Banner Card */}
        <Card className="overflow-hidden border-none shadow-xl bg-gradient-to-br from-indigo-50 to-white dark:from-slate-900 dark:to-slate-950">
          <div className="h-28 bg-gradient-to-r from-indigo-500/20 via-violet-500/10 to-transparent w-full" />

          <CardContent className="relative px-6 md:px-8 pb-6 pt-0">
            <div className="-mt-14 mb-4 relative z-10 flex flex-col md:flex-row items-center md:items-end justify-between gap-6">
              <div className="flex flex-col md:flex-row items-center md:items-end gap-5 text-center md:text-left">
                {/* Avatar */}
                <div className="w-28 h-28 rounded-2xl bg-white dark:bg-slate-800 p-2 shadow-lg flex-shrink-0 border border-indigo-100 dark:border-indigo-900/50">
                  <div className="w-full h-full bg-indigo-50 dark:bg-indigo-900/20 rounded-xl flex items-center justify-center text-indigo-400">
                    <User size={44} className="opacity-60" />
                  </div>
                </div>

                {/* Name / Info */}
                <div className="mb-1">
                  <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                    {user.name}
                  </h1>
                  <p className="text-indigo-600 dark:text-indigo-400 font-medium text-sm flex items-center justify-center md:justify-start gap-2 mt-1">
                    <Hash size={14} />
                    Roll No: {student.rollNo} &nbsp;•&nbsp; {student.className || "Class Not Assigned"}
                  </p>
                </div>
              </div>

              {/* Quick Stat Highlights */}
              <div className="flex items-center gap-3">
                <div className="px-4 py-2 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm text-center">
                  <span className="text-xs text-slate-400 font-medium block">Attempts</span>
                  <span className="text-base font-bold text-slate-800 dark:text-slate-100">{totalExamsAttempted}</span>
                </div>
                <div className="px-4 py-2 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm text-center">
                  <span className="text-xs text-slate-400 font-medium block">Avg Score</span>
                  <span className="text-base font-bold text-indigo-600 dark:text-indigo-400">{avgPercentage}%</span>
                </div>
              </div>
            </div>

            {/* Segmented Navigation Tabs */}
            <div className="flex border-b border-slate-200 dark:border-slate-800 mt-6 gap-2">
              <button
                onClick={() => setActiveTab("profile")}
                className={`pb-3 px-4 font-semibold text-sm transition-colors border-b-2 flex items-center gap-2 ${
                  activeTab === "profile"
                    ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                    : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                }`}
              >
                <User size={16} />
                Profile & Parents
              </button>
              <button
                onClick={() => setActiveTab("exams")}
                className={`pb-3 px-4 font-semibold text-sm transition-colors border-b-2 flex items-center gap-2 ${
                  activeTab === "exams"
                    ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                    : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                }`}
              >
                <ClipboardList size={16} />
                Exam Marks & Results
                {totalExamsAttempted > 0 && (
                  <span className="px-2 py-0.5 text-xs rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300">
                    {totalExamsAttempted}
                  </span>
                )}
              </button>
              <button
                onClick={() => setActiveTab("chat")}
                className={`pb-3 px-4 font-semibold text-sm transition-colors border-b-2 flex items-center gap-2 ${
                  activeTab === "chat"
                    ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                    : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                }`}
              >
                <MessageSquare size={16} />
                Direct Communication
              </button>
            </div>
          </CardContent>
        </Card>

        {/* Tab 1: Profile & Parents */}
        {activeTab === "profile" && (
          <div className="grid md:grid-cols-2 gap-6 animate-in fade-in duration-300">
            {/* Personal Details */}
            <Card className="p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                Personal Information
              </h3>
              <div className="space-y-3">
                <InfoRow icon={<Mail size={16} />} value={user.email} />
                <InfoRow icon={<Phone size={16} />} value={user.phoneNo || "No phone registered"} />
                <InfoRow
                  icon={<MapPin size={16} />}
                  value={
                    [user.city, user.state, user.country, user.pincode]
                      .filter(Boolean)
                      .join(", ") || "No address provided"
                  }
                />
                <InfoRow
                  icon={<Calendar size={16} />}
                  value={`Admission Date: ${fmt(student.dateOfAdmission)}`}
                />
              </div>

              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider pt-3">
                School & Class Enrolment
              </h3>
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 space-y-2">
                <DetailRow label="School" value={student.schoolName || "Assigned School"} />
                <DetailRow label="Class" value={student.className || "Assigned Class"} />
                <DetailRow label="Roll Number" value={student.rollNo} />
              </div>
            </Card>

            {/* Parent & Guardian Info */}
            <Card className="p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                <Users size={16} />
                Parent & Guardian Contacts
              </h3>
              <div className="space-y-4">
                {student.fatherName && (
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 space-y-1">
                    <p className="text-xs font-bold text-indigo-600 dark:text-indigo-400">👨 Father</p>
                    <DetailRow label="Name" value={student.fatherName} />
                    {student.fatherEmail && (
                      <DetailRow
                        label="Email"
                        value={<a href={`mailto:${student.fatherEmail}`} className="text-indigo-600 hover:underline">{student.fatherEmail}</a>}
                      />
                    )}
                    {student.fatherPhoneNo && <DetailRow label="Phone" value={student.fatherPhoneNo} />}
                  </div>
                )}

                {student.motherName && (
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 space-y-1">
                    <p className="text-xs font-bold text-indigo-600 dark:text-indigo-400">👩 Mother</p>
                    <DetailRow label="Name" value={student.motherName} />
                    {student.motherEmail && (
                      <DetailRow
                        label="Email"
                        value={<a href={`mailto:${student.motherEmail}`} className="text-indigo-600 hover:underline">{student.motherEmail}</a>}
                      />
                    )}
                    {student.motherPhoneNo && <DetailRow label="Phone" value={student.motherPhoneNo} />}
                  </div>
                )}

                {student.guardianName && (
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 space-y-1">
                    <p className="text-xs font-bold text-indigo-600 dark:text-indigo-400">
                      🛡️ Guardian ({student.guardianRelation || "Guardian"})
                    </p>
                    <DetailRow label="Name" value={student.guardianName} />
                    {student.guardianEmail && (
                      <DetailRow
                        label="Email"
                        value={<a href={`mailto:${student.guardianEmail}`} className="text-indigo-600 hover:underline">{student.guardianEmail}</a>}
                      />
                    )}
                    {student.guardianPhoneNo && <DetailRow label="Phone" value={student.guardianPhoneNo} />}
                  </div>
                )}

                {!student.fatherName && !student.motherName && !student.guardianName && (
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 text-center text-slate-400">
                    <p className="text-sm">No parent or guardian details on file.</p>
                  </div>
                )}
              </div>
            </Card>
          </div>
        )}

        {/* Tab 2: Exam Marks & Results */}
        {activeTab === "exams" && (
          <div className="space-y-6 animate-in fade-in duration-300">
            {loadingExams ? (
              <div className="p-12 text-center">
                <Spinner className="h-8 w-8 text-indigo-600 mx-auto" />
                <p className="mt-2 text-sm text-slate-500">Loading student exam records...</p>
              </div>
            ) : examHistory.length === 0 ? (
              <Card className="p-12 text-center border-dashed border-2 border-slate-200 dark:border-slate-800">
                <FileText className="mx-auto h-12 w-12 text-slate-300 dark:text-slate-600 mb-3" />
                <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-300">No Exam Records Found</h3>
                <p className="text-sm text-slate-500 max-w-sm mx-auto mt-1">
                  This student has not attempted any exams or quizzes yet.
                </p>
              </Card>
            ) : (
              <div className="overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 text-xs font-semibold uppercase text-slate-500">
                        <th className="py-3.5 px-4">Exam Name</th>
                        <th className="py-3.5 px-4">Subject</th>
                        <th className="py-3.5 px-4">Type</th>
                        <th className="py-3.5 px-4">Date</th>
                        <th className="py-3.5 px-4 text-center">Marks (Obtained / Max)</th>
                        <th className="py-3.5 px-4 text-center">Percentage</th>
                        <th className="py-3.5 px-4 text-center">Status</th>
                        <th className="py-3.5 px-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-sm">
                      {examHistory.map((exam) => (
                        <tr key={exam.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                          <td className="py-3.5 px-4 font-semibold text-slate-900 dark:text-slate-100">
                            {exam.examTitle}
                            <span className="block text-xs font-mono font-normal text-slate-400">
                              {exam.examCode}
                            </span>
                          </td>
                          <td className="py-3.5 px-4 text-slate-600 dark:text-slate-300">
                            {exam.subject || "General"}
                          </td>
                          <td className="py-3.5 px-4">
                            <Badge variant="outline" className="text-xs">
                              {exam.examType}
                            </Badge>
                          </td>
                          <td className="py-3.5 px-4 text-slate-500 text-xs">
                            {fmt(exam.submittedAt || exam.scheduledAt)}
                          </td>
                          <td className="py-3.5 px-4 text-center font-bold text-slate-800 dark:text-slate-100">
                            {exam.marksObtained} <span className="text-slate-400 font-normal">/ {exam.maxMarks}</span>
                          </td>
                          <td className="py-3.5 px-4 text-center">
                            <div className="inline-flex items-center gap-2">
                              <div className="w-16 h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                <div
                                  className={`h-full rounded-full ${
                                    exam.percentage >= 80
                                      ? "bg-emerald-500"
                                      : exam.percentage >= 50
                                      ? "bg-amber-500"
                                      : "bg-red-500"
                                  }`}
                                  style={{ width: `${Math.min(100, Math.max(0, exam.percentage))}%` }}
                                />
                              </div>
                              <span className="font-semibold text-xs text-slate-700 dark:text-slate-300">
                                {exam.percentage}%
                              </span>
                            </div>
                          </td>
                          <td className="py-3.5 px-4 text-center">
                            <span
                              className={`inline-flex px-2.5 py-1 rounded-full text-xs font-semibold ${
                                exam.status === "GRADED"
                                  ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
                                  : exam.status === "SUBMITTED"
                                  ? "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300"
                                  : "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300"
                              }`}
                            >
                              {exam.status}
                            </span>
                          </td>
                          <td className="py-3.5 px-4 text-right">
                            <Link href={`/teacher/exams/${exam.examId}/results`}>
                              <Button variant="ghost" size="sm" className="text-indigo-600 hover:text-indigo-800">
                                Exam Results
                              </Button>
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Direct Communication */}
        {activeTab === "chat" && (
          <Card className="p-8 border border-slate-200 dark:border-slate-800 shadow-sm text-center space-y-4 animate-in fade-in duration-300">
            <div className="w-16 h-16 rounded-2xl bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 flex items-center justify-center mx-auto shadow-inner">
              <MessageSquare size={32} />
            </div>
            <div className="max-w-md mx-auto space-y-2">
              <h3 className="text-xl font-bold text-slate-800 dark:text-slate-100">
                Chat with {user.name}
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Initiate a 1-on-1 instant chat session with this student for performance feedback, guidance, or academic support.
              </p>
            </div>
            <div className="pt-2">
              <Link href={`/chat?userId=${user.id}`}>
                <Button variant="primary" size="lg" className="shadow-glow px-8">
                  <MessageSquare className="mr-2 h-4 w-4" />
                  Launch Direct Chat
                </Button>
              </Link>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

/* ─── Small helpers ───────────────────────────────────────────── */

function InfoRow({
  icon,
  value,
}: {
  icon: React.ReactNode;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-3 text-slate-700 dark:text-slate-300">
      <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500 flex-shrink-0 mt-0.5">
        {icon}
      </div>
      <span className="mt-1 leading-relaxed text-sm">{value}</span>
    </div>
  );
}

function DetailRow({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-xs text-slate-500 shrink-0">{label}</span>
      <span className="text-sm font-medium text-slate-800 dark:text-slate-200 text-right">
        {value}
      </span>
    </div>
  );
}
