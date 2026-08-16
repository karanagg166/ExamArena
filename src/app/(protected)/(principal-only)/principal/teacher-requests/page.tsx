"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  UserCheck,
  UserX,
  Clock,
  CheckCircle2,
  XCircle,
  Building2,
  Calendar,
  BookOpen,
  ArrowLeft,
  Search,
  Hash,
  GraduationCap,
  RefreshCw,
  Plus,
} from "lucide-react";

import { PageHeader } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/loading";
import {
  useJoinRequestStore,
  useTeacherRequestStore,
} from "@/stores";
import { api } from "@/lib/axios";
import type { ClassJoinRequest } from "@/types";

function PrincipalTeacherRequestsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tabParam = searchParams.get("tab");

  const [schoolId, setSchoolId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Top Section Category Tab: TEACHER_SCHOOL | TEACHER_CLASS | STUDENT_ENROLLMENT
  const [category, setCategory] = useState<
    "TEACHER_SCHOOL" | "TEACHER_CLASS" | "STUDENT_ENROLLMENT"
  >(() => {
    if (tabParam === "student" || tabParam === "students") return "STUDENT_ENROLLMENT";
    if (tabParam === "teaching" || tabParam === "class" || tabParam === "classes") return "TEACHER_CLASS";
    return "TEACHER_SCHOOL";
  });

  useEffect(() => {
    if (tabParam === "student" || tabParam === "students") setCategory("STUDENT_ENROLLMENT");
    else if (tabParam === "teaching" || tabParam === "class" || tabParam === "classes") setCategory("TEACHER_CLASS");
    else if (tabParam === "faculty" || tabParam === "teacher" || tabParam === "teachers") setCategory("TEACHER_SCHOOL");
  }, [tabParam]);

  // Status Tab: ALL | PENDING | APPROVED | REJECTED
  const [statusTab, setStatusTab] = useState<"ALL" | "PENDING" | "APPROVED" | "REJECTED">(
    "PENDING"
  );
  const [search, setSearch] = useState("");

  // Student Roll Number Approval Modal state
  const [approvingStudentReq, setApprovingStudentReq] = useState<ClassJoinRequest | null>(null);
  const [rollNoMode, setRollNoMode] = useState<"AUTO" | "CUSTOM">("AUTO");
  const [customRollNo, setCustomRollNo] = useState("");
  const [studentActionError, setStudentActionError] = useState<string | null>(null);

  const {
    schoolTeacherSchoolRequests,
    schoolTeacherClassRequests,
    fetchSchoolTeacherSchoolRequests,
    fetchSchoolTeacherClassRequests,
    decideTeacherSchoolRequest,
    decideTeacherClassRequest,
  } = useTeacherRequestStore();

  const {
    schoolRequests: studentRequests,
    fetchSchoolRequests: fetchStudentRequests,
    decideRequest: decideStudentRequest,
  } = useJoinRequestStore();

  const loadData = useCallback(async (silent = false) => {
    if (!silent) {
      setLoading(true);
      setError(null);
    }
    try {
      const schoolRes = await api.get<{ id: string }>("/api/v1/schools/me");
      const sid = schoolRes.data?.id;
      setSchoolId(sid || null);

      if (sid) {
        await Promise.allSettled([
          fetchSchoolTeacherSchoolRequests(sid),
          fetchSchoolTeacherClassRequests(sid),
          fetchStudentRequests(sid),
        ]);
      }
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 404) {
        setSchoolId(null);
      } else {
        const detail =
          (err as { response?: { data?: { detail?: string } } })?.response?.data
            ?.detail;
        if (!silent) {
          setError(detail ?? "Failed to load school requests.");
        }
      }
    } finally {
      if (!silent) setLoading(false);
    }
  }, [
    fetchSchoolTeacherSchoolRequests,
    fetchSchoolTeacherClassRequests,
    fetchStudentRequests,
  ]);

  useEffect(() => {
    loadData(false);

    // Auto-poll every 12 seconds for real-time join request updates
    const interval = setInterval(() => {
      loadData(true);
    }, 12000);

    return () => clearInterval(interval);
  }, [loadData]);

  // Handler for Teacher School Request Decision
  const handleDecideTeacherSchool = async (
    requestId: string,
    status: "APPROVED" | "REJECTED"
  ) => {
    setProcessingId(requestId);
    const res = await decideTeacherSchoolRequest(requestId, status);
    if (!res.success) {
      alert(res.error || "Failed to update teacher school request");
    }
    setProcessingId(null);
  };

  // Handler for Teacher Class Request Decision
  const handleDecideTeacherClass = async (
    requestId: string,
    status: "APPROVED" | "REJECTED"
  ) => {
    setProcessingId(requestId);
    const res = await decideTeacherClassRequest(requestId, status);
    if (!res.success) {
      alert(res.error || "Failed to update teacher class request");
    }
    setProcessingId(null);
  };

  // Handler for Student Request Decision
  const handleOpenStudentApproveModal = (req: ClassJoinRequest) => {
    setApprovingStudentReq(req);
    setRollNoMode("AUTO");
    setCustomRollNo("");
    setStudentActionError(null);
  };

  const handleConfirmStudentApprove = async () => {
    if (!approvingStudentReq) return;
    setProcessingId(approvingStudentReq.id);
    setStudentActionError(null);

    const cleanedRollNo = rollNoMode === "CUSTOM" ? customRollNo.trim().replace(/\D/g, "") : undefined;
    if (rollNoMode === "CUSTOM" && !cleanedRollNo) {
      setStudentActionError("Please enter a numeric roll number (numbers only) or choose Auto.");
      setProcessingId(null);
      return;
    }

    const payload = {
      rollNo: rollNoMode === "CUSTOM" ? cleanedRollNo : undefined,
      autoRollNo: rollNoMode === "AUTO",
    };

    const res = await decideStudentRequest(
      approvingStudentReq.id,
      "APPROVED",
      payload
    );

    if (res.success) {
      setApprovingStudentReq(null);
      if (schoolId) fetchStudentRequests(schoolId);
    } else {
      setStudentActionError(res.error || "Failed to approve student request");
    }
    setProcessingId(null);
  };

  const handleRejectStudent = async (requestId: string) => {
    setProcessingId(requestId);
    const res = await decideStudentRequest(requestId, "REJECTED");
    if (!res.success) {
      alert(res.error || "Failed to reject student request");
    } else if (schoolId) {
      fetchStudentRequests(schoolId);
    }
    setProcessingId(null);
  };

  // Filtered lists
  const pendingTeacherSchoolCount = schoolTeacherSchoolRequests.filter(
    (r) => r.status === "PENDING"
  ).length;
  const pendingTeacherClassCount = schoolTeacherClassRequests.filter(
    (r) => r.status === "PENDING"
  ).length;
  const pendingStudentCount = studentRequests.filter(
    (r) => r.status === "PENDING"
  ).length;

  const filteredTeacherSchool = schoolTeacherSchoolRequests.filter((r) => {
    if (statusTab !== "ALL" && r.status !== statusTab) return false;
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      r.teacherName.toLowerCase().includes(q) ||
      r.teacherEmail.toLowerCase().includes(q) ||
      (r.teacherDepartment && r.teacherDepartment.toLowerCase().includes(q))
    );
  });

  const filteredTeacherClass = schoolTeacherClassRequests.filter((r) => {
    if (statusTab !== "ALL" && r.status !== statusTab) return false;
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      r.teacherName.toLowerCase().includes(q) ||
      r.teacherEmail.toLowerCase().includes(q) ||
      r.className.toLowerCase().includes(q)
    );
  });

  const filteredStudents = studentRequests.filter((r) => {
    if (statusTab !== "ALL" && r.status !== statusTab) return false;
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      r.studentName.toLowerCase().includes(q) ||
      r.studentEmail.toLowerCase().includes(q) ||
      r.className.toLowerCase().includes(q)
    );
  });

  return (
    <div className="page-shell">
      <div className="max-w-6xl mx-auto space-y-8 animate-fade-in-up">
        <PageHeader
          overline="School Administration"
          title="School Requests & Admissions"
          subtitle="Manage incoming faculty join requests, teaching class assignments, and student enrollment approvals in real-time."
          actions={
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadData(false)}
                disabled={loading}
                className="flex items-center gap-2 text-xs"
              >
                <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push("/principal")}
                className="flex items-center gap-2 text-xs"
              >
                <ArrowLeft size={14} /> Back to Dashboard
              </Button>
            </div>
          }
        />

        {/* Primary Category Selector */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <button
            onClick={() => {
              setCategory("TEACHER_SCHOOL");
              setStatusTab("PENDING");
            }}
            className={`p-4 rounded-2xl border text-left transition-all ${
              category === "TEACHER_SCHOOL"
                ? "border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/20 shadow-sm"
                : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300"
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400">
                  <Building2 size={18} />
                </div>
                <span className="font-bold text-sm text-slate-900 dark:text-slate-100">
                  Faculty Join Requests
                </span>
              </div>
              {pendingTeacherSchoolCount > 0 && (
                <span className="px-2.5 py-0.5 text-xs rounded-full bg-amber-500 text-white font-bold">
                  {pendingTeacherSchoolCount}
                </span>
              )}
            </div>
            <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
              Teachers requesting to join your school
            </p>
          </button>

          <button
            onClick={() => {
              setCategory("TEACHER_CLASS");
              setStatusTab("PENDING");
            }}
            className={`p-4 rounded-2xl border text-left transition-all ${
              category === "TEACHER_CLASS"
                ? "border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/20 shadow-sm"
                : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300"
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-emerald-100 dark:bg-emerald-900/50 text-emerald-600 dark:text-emerald-400">
                  <BookOpen size={18} />
                </div>
                <span className="font-bold text-sm text-slate-900 dark:text-slate-100">
                  Class Teaching Requests
                </span>
              </div>
              {pendingTeacherClassCount > 0 && (
                <span className="px-2.5 py-0.5 text-xs rounded-full bg-amber-500 text-white font-bold">
                  {pendingTeacherClassCount}
                </span>
              )}
            </div>
            <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
              Faculty requesting to teach classes
            </p>
          </button>

          <button
            onClick={() => {
              setCategory("STUDENT_ENROLLMENT");
              setStatusTab("PENDING");
            }}
            className={`p-4 rounded-2xl border text-left transition-all ${
              category === "STUDENT_ENROLLMENT"
                ? "border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/20 shadow-sm"
                : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300"
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400">
                  <GraduationCap size={18} />
                </div>
                <span className="font-bold text-sm text-slate-900 dark:text-slate-100">
                  Student Admissions
                </span>
              </div>
              {pendingStudentCount > 0 && (
                <span className="px-2.5 py-0.5 text-xs rounded-full bg-amber-500 text-white font-bold">
                  {pendingStudentCount}
                </span>
              )}
            </div>
            <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
              Class enrollment & roll number assignment
            </p>
          </button>
        </div>

        {/* Tab & Search Bar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
          <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-xl gap-1">
            <button
              onClick={() => setStatusTab("PENDING")}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 ${
                statusTab === "PENDING"
                  ? "bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm"
                  : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
              }`}
            >
              <Clock size={15} />
              Pending
            </button>
            <button
              onClick={() => setStatusTab("APPROVED")}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 ${
                statusTab === "APPROVED"
                  ? "bg-white dark:bg-slate-900 text-emerald-600 dark:text-emerald-400 shadow-sm"
                  : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
              }`}
            >
              <CheckCircle2 size={15} />
              Approved
            </button>
            <button
              onClick={() => setStatusTab("REJECTED")}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 ${
                statusTab === "REJECTED"
                  ? "bg-white dark:bg-slate-900 text-red-600 dark:text-red-400 shadow-sm"
                  : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
              }`}
            >
              <XCircle size={15} />
              Rejected
            </button>
            <button
              onClick={() => setStatusTab("ALL")}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
                statusTab === "ALL"
                  ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm"
                  : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
              }`}
            >
              All
            </button>
          </div>

          <div className="relative max-w-xs w-full">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by name, email, class..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        {/* List Content */}
        {loading ? (
          <div className="py-20 text-center">
            <Spinner className="h-8 w-8 text-indigo-600 mx-auto" />
            <p className="mt-2 text-sm text-slate-500">Loading requests...</p>
          </div>
        ) : !schoolId ? (
          <GlassCard padding="lg" className="text-center py-16 space-y-4 max-w-lg mx-auto">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Building2 className="h-8 w-8" />
            </div>
            <div className="space-y-1">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                No School Associated Yet
              </h3>
              <p className="text-sm text-slate-500 dark:text-zinc-400">
                You must establish or join a school before receiving faculty and student enrollment requests.
              </p>
            </div>
            <div className="flex items-center justify-center gap-3 pt-2">
              <Button onClick={() => router.push("/signup/principal/create-school")} className="bg-indigo-600 hover:bg-indigo-700 text-white">
                <Plus className="mr-2 h-4 w-4" /> Create School
              </Button>
              <Button variant="outline" onClick={() => loadData(false)}>
                <RefreshCw className="mr-2 h-4 w-4" /> Refresh
              </Button>
            </div>
          </GlassCard>
        ) : error ? (
          <GlassCard padding="lg" className="text-center py-12 space-y-3">
            <p className="text-red-500 font-bold">{error}</p>
            <Button onClick={() => loadData(false)} variant="outline" size="sm">
              Retry
            </Button>
          </GlassCard>
        ) : category === "TEACHER_SCHOOL" ? (
          filteredTeacherSchool.length === 0 ? (
            <GlassCard padding="lg" className="text-center py-16 space-y-3">
              <Building2 size={40} className="mx-auto text-slate-300 dark:text-slate-600" />
              <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-300">
                No Faculty Join Requests
              </h3>
              <p className="text-sm text-slate-500 max-w-sm mx-auto">
                No teachers currently have join requests under the selected status.
              </p>
            </GlassCard>
          ) : (
            <div className="grid gap-4">
              {filteredTeacherSchool.map((req) => (
                <GlassCard
                  key={req.id}
                  padding="md"
                  className="flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-indigo-200 dark:hover:border-indigo-900/50 transition-colors"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-3">
                      <h4 className="font-bold text-slate-900 dark:text-slate-100 text-base">
                        {req.teacherName}
                      </h4>
                      <Badge
                        variant={
                          req.status === "APPROVED"
                            ? "success"
                            : req.status === "REJECTED"
                            ? "danger"
                            : "warning"
                        }
                      >
                        {req.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {req.teacherEmail}
                    </p>
                    <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 dark:text-slate-300 pt-1">
                      {req.teacherDepartment && (
                        <span className="flex items-center gap-1 text-slate-500">
                          Dept: {req.teacherDepartment}
                        </span>
                      )}
                      <span className="flex items-center gap-1 text-slate-400">
                        <Calendar size={13} />
                        Requested on {new Date(req.requestedAt).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  {req.status === "PENDING" && (
                    <div className="flex items-center gap-2 self-end md:self-center">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={processingId === req.id}
                        onClick={() => handleDecideTeacherSchool(req.id, "REJECTED")}
                        className="border-red-200 text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30"
                      >
                        <UserX size={15} className="mr-1.5" />
                        Decline
                      </Button>
                      <Button
                        size="sm"
                        variant="primary"
                        disabled={processingId === req.id}
                        onClick={() => handleDecideTeacherSchool(req.id, "APPROVED")}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm"
                      >
                        <UserCheck size={15} className="mr-1.5" />
                        Accept Faculty
                      </Button>
                    </div>
                  )}
                </GlassCard>
              ))}
            </div>
          )
        ) : category === "TEACHER_CLASS" ? (
          filteredTeacherClass.length === 0 ? (
            <GlassCard padding="lg" className="text-center py-16 space-y-3">
              <BookOpen size={40} className="mx-auto text-slate-300 dark:text-slate-600" />
              <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-300">
                No Class Teaching Requests
              </h3>
              <p className="text-sm text-slate-500 max-w-sm mx-auto">
                No teachers currently have class teaching requests under this status.
              </p>
            </GlassCard>
          ) : (
            <div className="grid gap-4">
              {filteredTeacherClass.map((req) => (
                <GlassCard
                  key={req.id}
                  padding="md"
                  className="flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-indigo-200 dark:hover:border-indigo-900/50 transition-colors"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-3">
                      <h4 className="font-bold text-slate-900 dark:text-slate-100 text-base">
                        {req.teacherName}
                      </h4>
                      <Badge
                        variant={
                          req.status === "APPROVED"
                            ? "success"
                            : req.status === "REJECTED"
                            ? "danger"
                            : "warning"
                        }
                      >
                        {req.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {req.teacherEmail}
                    </p>
                    <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 dark:text-slate-300 pt-1">
                      <span className="flex items-center gap-1 font-semibold text-indigo-600 dark:text-indigo-400">
                        <BookOpen size={14} /> Class: {req.className}
                      </span>
                      {req.subject && (
                        <span className="flex items-center gap-1 text-slate-500">
                          Subject: {req.subject}
                        </span>
                      )}
                      <span className="flex items-center gap-1 text-slate-400">
                        <Calendar size={13} />
                        Requested on {new Date(req.requestedAt).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  {req.status === "PENDING" && (
                    <div className="flex items-center gap-2 self-end md:self-center">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={processingId === req.id}
                        onClick={() => handleDecideTeacherClass(req.id, "REJECTED")}
                        className="border-red-200 text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30"
                      >
                        <UserX size={15} className="mr-1.5" />
                        Reject
                      </Button>
                      <Button
                        size="sm"
                        variant="primary"
                        disabled={processingId === req.id}
                        onClick={() => handleDecideTeacherClass(req.id, "APPROVED")}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm"
                      >
                        <UserCheck size={15} className="mr-1.5" />
                        Approve & Assign
                      </Button>
                    </div>
                  )}
                </GlassCard>
              ))}
            </div>
          )
        ) : (
          filteredStudents.length === 0 ? (
            <GlassCard padding="lg" className="text-center py-16 space-y-3">
              <GraduationCap size={40} className="mx-auto text-slate-300 dark:text-slate-600" />
              <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-300">
                No Student Admission Requests
              </h3>
              <p className="text-sm text-slate-500 max-w-sm mx-auto">
                No student class enrollment requests under the selected status.
              </p>
            </GlassCard>
          ) : (
            <div className="grid gap-4">
              {filteredStudents.map((req) => (
                <GlassCard
                  key={req.id}
                  padding="md"
                  className="flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-indigo-200 dark:hover:border-indigo-900/50 transition-colors"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-3">
                      <h4 className="font-bold text-slate-900 dark:text-slate-100 text-base">
                        {req.studentName}
                      </h4>
                      <Badge
                        variant={
                          req.status === "APPROVED"
                            ? "success"
                            : req.status === "REJECTED"
                            ? "danger"
                            : "warning"
                        }
                      >
                        {req.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {req.studentEmail}
                    </p>
                    <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 dark:text-slate-300 pt-1">
                      <span className="flex items-center gap-1 font-semibold text-blue-600 dark:text-blue-400">
                        <BookOpen size={14} /> Class: {req.className}
                      </span>
                      <span className="flex items-center gap-1 text-slate-400">
                        <Calendar size={13} />
                        Requested on {new Date(req.requestedAt).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  {req.status === "PENDING" && (
                    <div className="flex items-center gap-2 self-end md:self-center">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={processingId === req.id}
                        onClick={() => handleRejectStudent(req.id)}
                        className="border-red-200 text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30"
                      >
                        <UserX size={15} className="mr-1.5" />
                        Reject
                      </Button>
                      <Button
                        size="sm"
                        variant="primary"
                        disabled={processingId === req.id}
                        onClick={() => handleOpenStudentApproveModal(req)}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm"
                      >
                        <UserCheck size={15} className="mr-1.5" />
                        Approve & Assign Roll No
                      </Button>
                    </div>
                  )}
                </GlassCard>
              ))}
            </div>
          )
        )}

        {/* Student Enrollment & Roll Number Modal */}
        {approvingStudentReq && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-3xl p-6 shadow-2xl border border-slate-200 dark:border-slate-800 space-y-5 animate-in zoom-in-95 duration-200">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                    Approve Student Enrollment
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Assign student to <strong>{approvingStudentReq.className}</strong>
                  </p>
                </div>
                <button
                  onClick={() => setApprovingStudentReq(null)}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                  ✕
                </button>
              </div>

              <div className="rounded-xl bg-slate-50 dark:bg-slate-800/50 p-3.5 border border-slate-200 dark:border-slate-800 text-xs space-y-1">
                <p>
                  <strong>Student:</strong> {approvingStudentReq.studentName}
                </p>
                <p>
                  <strong>Email:</strong> {approvingStudentReq.studentEmail}
                </p>
                <p className="text-amber-600 dark:text-amber-400 font-semibold pt-1">
                  Note: Roll numbers cannot be changed once assigned.
                </p>
              </div>

              {studentActionError && (
                <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300">
                  {studentActionError}
                </div>
              )}

              <div className="space-y-3">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                  Roll Number Assignment
                </label>

                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setRollNoMode("AUTO")}
                    className={`p-3 rounded-xl border text-left text-xs font-semibold transition-all ${
                      rollNoMode === "AUTO"
                        ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-400 ring-2 ring-indigo-500/20"
                        : "border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400"
                    }`}
                  >
                    Automatic Next
                    <p className="text-[10px] font-normal text-slate-500 mt-0.5">
                      Sequential roll number
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setRollNoMode("CUSTOM")}
                    className={`p-3 rounded-xl border text-left text-xs font-semibold transition-all ${
                      rollNoMode === "CUSTOM"
                        ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-400 ring-2 ring-indigo-500/20"
                        : "border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400"
                    }`}
                  >
                    Custom Roll No
                    <p className="text-[10px] font-normal text-slate-500 mt-0.5">
                      Enter manual number
                    </p>
                  </button>
                </div>

                {rollNoMode === "CUSTOM" && (
                  <div className="space-y-1.5 pt-1">
                    <label className="text-xs text-slate-600 dark:text-slate-400">
                      Enter Roll Number
                    </label>
                    <div className="relative">
                      <Hash size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                      <input
                        type="text"
                        inputMode="numeric"
                        pattern="[0-9]*"
                        value={customRollNo}
                        onChange={(e) => setCustomRollNo(e.target.value.replace(/\D/g, ""))}
                        placeholder="e.g. 101, 102 (numbers only)"
                        className="w-full pl-8 pr-4 py-2 text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setApprovingStudentReq(null)}
                  disabled={processingId === approvingStudentReq.id}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                  onClick={handleConfirmStudentApprove}
                  disabled={processingId === approvingStudentReq.id}
                >
                  {processingId === approvingStudentReq.id ? "Enrolling..." : "Confirm & Enroll"}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function PrincipalTeacherRequestsPage() {
  return (
    <React.Suspense
      fallback={
        <div className="flex min-h-[60vh] items-center justify-center">
          <Spinner className="h-8 w-8 border-4" />
        </div>
      }
    >
      <PrincipalTeacherRequestsContent />
    </React.Suspense>
  );
}

