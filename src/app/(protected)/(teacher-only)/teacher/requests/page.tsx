"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  UserCheck,
  UserX,
  Clock,
  Building2,
  Calendar,
  BookOpen,
  ArrowLeft,
  Search,
  GraduationCap,
  RefreshCw,
  Plus,
  ArrowRight,
  School,
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
import { toast } from "sonner";

export default function TeacherRequestsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tabParam = searchParams.get("tab");

  const [schoolId, setSchoolId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [, setError] = useState<string | null>(null);

  // Top Category Tab: STUDENT_ENROLLMENT | MY_SCHOOL_JOIN | MY_CLASS_TEACHING
  const [category, setCategory] = useState<
    "STUDENT_ENROLLMENT" | "MY_SCHOOL_JOIN" | "MY_CLASS_TEACHING"
  >(() => {
    if (tabParam === "school" || tabParam === "join-school") return "MY_SCHOOL_JOIN";
    if (tabParam === "teaching" || tabParam === "classes") return "MY_CLASS_TEACHING";
    return "STUDENT_ENROLLMENT";
  });

  useEffect(() => {
    if (tabParam === "school" || tabParam === "join-school") setCategory("MY_SCHOOL_JOIN");
    else if (tabParam === "teaching" || tabParam === "classes") setCategory("MY_CLASS_TEACHING");
    else if (tabParam === "student" || tabParam === "students") setCategory("STUDENT_ENROLLMENT");
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
  const [actionError, setActionError] = useState<string | null>(null);

  const {
    mySchoolRequests,
    myClassRequests,
    fetchMySchoolRequests,
    fetchMyClassRequests,
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
      const teacherRes = await api.get<{ schoolId?: string }>("/api/v1/teachers/me");
      const sid = teacherRes.data?.schoolId;
      setSchoolId(sid || null);

      await Promise.allSettled([
        fetchMySchoolRequests(),
        fetchMyClassRequests(),
        sid ? fetchStudentRequests(sid) : Promise.resolve(),
      ]);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response
          ?.data?.detail;
      setError(detail ?? "Failed to load requests.");
    } finally {
      setLoading(false);
    }
  }, [fetchMySchoolRequests, fetchMyClassRequests, fetchStudentRequests]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Student request handlers
  const handleDecideStudent = async (status: "APPROVED" | "REJECTED") => {
    if (!approvingStudentReq) return;
    setProcessingId(approvingStudentReq.id);
    setActionError(null);
    try {
      const result = await decideStudentRequest(approvingStudentReq.id, status, {
        autoRollNo: rollNoMode === "AUTO",
        rollNo: rollNoMode === "CUSTOM" ? customRollNo.trim() : undefined,
      });
      if (result.success) {
        toast.success(`Request ${status.toLowerCase()} successfully`);
        setApprovingStudentReq(null);
        setCustomRollNo("");
        if (schoolId) await fetchStudentRequests(schoolId);
      } else {
        setActionError(result.error ?? "Failed to process request");
      }
    } catch {
      setActionError("Unexpected error occurred while processing request.");
    } finally {
      setProcessingId(null);
    }
  };

  const pendingStudentCount = studentRequests.filter((r) => r.status === "PENDING").length;
  const pendingMySchoolCount = mySchoolRequests.filter((r) => r.status === "PENDING").length;
  const pendingMyClassCount = myClassRequests.filter((r) => r.status === "PENDING").length;

  const filteredStudents = studentRequests.filter((r) => {
    const matchesStatus = statusTab === "ALL" || r.status === statusTab;
    const matchesSearch =
      !search.trim() ||
      r.studentName?.toLowerCase().includes(search.toLowerCase()) ||
      r.studentEmail?.toLowerCase().includes(search.toLowerCase()) ||
      r.className?.toLowerCase().includes(search.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  return (
    <div className="page-shell space-y-8">
      <div className="max-w-6xl mx-auto space-y-8 animate-fade-in-up">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                className="text-zinc-400 hover:text-white pl-0"
                onClick={() => router.push("/dashboard")}
              >
                <ArrowLeft className="w-4 h-4 mr-1.5" /> Back to Dashboard
              </Button>
            </div>
            <PageHeader
              overline="Teacher Approvals & Requests"
              title="Requests & Approvals Command Center"
              subtitle="Approve student class enrollments, track your school join status, and review class teaching assignments."
            />
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadData(true)}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} /> Refresh
            </Button>
          </div>
        </div>

        {/* Category Tab Switcher */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 border-b border-zinc-800 pb-4">
          <button
            type="button"
            onClick={() => {
              setCategory("STUDENT_ENROLLMENT");
              setStatusTab("PENDING");
            }}
            className={`flex items-center justify-between p-4 rounded-2xl border text-left transition-all ${
              category === "STUDENT_ENROLLMENT"
                ? "bg-indigo-500/15 border-indigo-500/40 text-white shadow-sm"
                : "bg-zinc-900/40 border-zinc-800 text-zinc-400 hover:border-zinc-700 hover:text-zinc-200"
            }`}
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400">
                <GraduationCap className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-bold">Student Class Enrollments</p>
                <p className="text-xs text-zinc-400">Students joining with code</p>
              </div>
            </div>
            {pendingStudentCount > 0 && (
              <Badge variant="warning" className="text-xs">
                {pendingStudentCount} Pending
              </Badge>
            )}
          </button>

          <button
            type="button"
            onClick={() => {
              setCategory("MY_SCHOOL_JOIN");
              setStatusTab("ALL");
            }}
            className={`flex items-center justify-between p-4 rounded-2xl border text-left transition-all ${
              category === "MY_SCHOOL_JOIN"
                ? "bg-emerald-500/15 border-emerald-500/40 text-white shadow-sm"
                : "bg-zinc-900/40 border-zinc-800 text-zinc-400 hover:border-zinc-700 hover:text-zinc-200"
            }`}
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400">
                <School className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-bold">My School Join Status</p>
                <p className="text-xs text-zinc-400">Institutional membership</p>
              </div>
            </div>
            {pendingMySchoolCount > 0 && (
              <Badge variant="warning" className="text-xs">
                {pendingMySchoolCount}
              </Badge>
            )}
          </button>

          <button
            type="button"
            onClick={() => {
              setCategory("MY_CLASS_TEACHING");
              setStatusTab("ALL");
            }}
            className={`flex items-center justify-between p-4 rounded-2xl border text-left transition-all ${
              category === "MY_CLASS_TEACHING"
                ? "bg-violet-500/15 border-violet-500/40 text-white shadow-sm"
                : "bg-zinc-900/40 border-zinc-800 text-zinc-400 hover:border-zinc-700 hover:text-zinc-200"
            }`}
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-violet-500/20 text-violet-400">
                <BookOpen className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-bold">Class Teaching Requests</p>
                <p className="text-xs text-zinc-400">Classes you requested</p>
              </div>
            </div>
            {pendingMyClassCount > 0 && (
              <Badge variant="warning" className="text-xs">
                {pendingMyClassCount}
              </Badge>
            )}
          </button>
        </div>

        {/* ─── TAB 1: STUDENT ENROLLMENT REQUESTS ─── */}
        {category === "STUDENT_ENROLLMENT" && (
          <div className="space-y-6">
            {/* Filter Bar */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
              <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
                {(["ALL", "PENDING", "APPROVED", "REJECTED"] as const).map((st) => (
                  <button
                    key={st}
                    type="button"
                    onClick={() => setStatusTab(st)}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
                      statusTab === st
                        ? "bg-indigo-600 text-white"
                        : "bg-zinc-800/70 text-zinc-400 hover:text-white"
                    }`}
                  >
                    {st === "ALL" ? "All Requests" : st}
                    {st === "PENDING" && pendingStudentCount > 0 && ` (${pendingStudentCount})`}
                  </button>
                ))}
              </div>

              <div className="relative max-w-xs w-full">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
                <input
                  type="text"
                  placeholder="Search student or class..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 rounded-xl border border-zinc-800 bg-zinc-900 text-xs text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            {loading ? (
              <div className="flex min-h-[30vh] items-center justify-center">
                <Spinner className="h-8 w-8 border-4" />
              </div>
            ) : filteredStudents.length === 0 ? (
              <GlassCard padding="lg" className="text-center py-12 text-zinc-400 space-y-3">
                <GraduationCap size={36} className="mx-auto text-zinc-600" />
                <p className="text-base font-semibold text-zinc-200">No Student Enrollment Requests</p>
                <p className="text-xs text-zinc-500 max-w-md mx-auto">
                  When students enter your 8-character class join code, their enrollment applications will appear right here for approval.
                </p>
                <Link href="/teacher/classes">
                  <Button size="sm" variant="outline" className="mt-2 text-xs">
                    View Class Join Codes <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Button>
                </Link>
              </GlassCard>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredStudents.map((req) => (
                  <div
                    key={req.id}
                    className="p-5 rounded-2xl border border-zinc-800 bg-zinc-900/60 space-y-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h4 className="text-base font-bold text-white">{req.studentName || "Student"}</h4>
                        <p className="text-xs text-zinc-400">{req.studentEmail}</p>
                        <p className="text-xs text-indigo-400 font-semibold mt-1">
                          Class: {req.className || "Assigned Class"}
                        </p>
                      </div>
                      <Badge
                        variant={
                          req.status === "APPROVED"
                            ? "success"
                            : req.status === "PENDING"
                            ? "warning"
                            : "destructive"
                        }
                      >
                        {req.status}
                      </Badge>
                    </div>

                    <div className="text-xs text-zinc-500 flex items-center gap-1.5">
                      <Calendar size={13} />
                      Requested on {new Date(req.requestedAt).toLocaleDateString()}
                    </div>

                    {req.status === "PENDING" && (
                      <div className="flex items-center gap-2 pt-2 border-t border-zinc-800/80">
                        <Button
                          size="sm"
                          className="w-full bg-emerald-600 hover:bg-emerald-700 text-white text-xs"
                          onClick={() => {
                            setApprovingStudentReq(req);
                            setRollNoMode("AUTO");
                            setCustomRollNo("");
                            setActionError(null);
                          }}
                        >
                          <UserCheck className="w-3.5 h-3.5 mr-1" /> Approve Request
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          className="w-full text-xs"
                          onClick={() => {
                            setApprovingStudentReq(req);
                            handleDecideStudent("REJECTED");
                          }}
                        >
                          <UserX className="w-3.5 h-3.5 mr-1" /> Reject
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ─── TAB 2: MY SCHOOL JOIN STATUS ─── */}
        {category === "MY_SCHOOL_JOIN" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-white">Your School Affiliation</h3>
                <p className="text-xs text-zinc-400">Track and manage your requests to join educational institutions.</p>
              </div>
              <Link href="/teacher/school/join">
                <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs">
                  <Plus className="w-3.5 h-3.5 mr-1" /> Browse Schools to Join
                </Button>
              </Link>
            </div>

            {mySchoolRequests.length === 0 ? (
              <GlassCard padding="lg" className="text-center py-12 text-zinc-400 space-y-3">
                <Building2 size={36} className="mx-auto text-zinc-600" />
                <p className="text-base font-semibold text-zinc-200">No School Join Requests</p>
                <p className="text-xs text-zinc-500 max-w-md mx-auto">
                  You have not submitted any join requests to schools yet. Browse registered institutions to join their faculty.
                </p>
                <Link href="/teacher/school/join">
                  <Button size="sm" variant="outline" className="mt-2 text-xs">
                    Browse Schools <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Button>
                </Link>
              </GlassCard>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {mySchoolRequests.map((req) => (
                  <div
                    key={req.id}
                    className="p-5 rounded-2xl border border-zinc-800 bg-zinc-900/60 space-y-3"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h4 className="text-base font-bold text-white">{req.schoolName}</h4>
                        <p className="text-xs text-zinc-400">School ID: {req.schoolId}</p>
                      </div>
                      <Badge
                        variant={
                          req.status === "APPROVED"
                            ? "success"
                            : req.status === "PENDING"
                            ? "warning"
                            : "destructive"
                        }
                      >
                        {req.status}
                      </Badge>
                    </div>

                    <div className="text-xs text-zinc-500 flex items-center gap-1.5 pt-2 border-t border-zinc-800">
                      <Clock size={13} />
                      Status: {req.status} • Submitted on {new Date(req.requestedAt).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ─── TAB 3: MY CLASS TEACHING REQUESTS ─── */}
        {category === "MY_CLASS_TEACHING" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-white">Class Teaching Requests</h3>
                <p className="text-xs text-zinc-400">Classes you have requested to teach sent to your Principal.</p>
              </div>
              <Link href="/teacher/classes">
                <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs">
                  <GraduationCap className="w-3.5 h-3.5 mr-1" /> Request New Class
                </Button>
              </Link>
            </div>

            {myClassRequests.length === 0 ? (
              <GlassCard padding="lg" className="text-center py-12 text-zinc-400 space-y-3">
                <BookOpen size={36} className="mx-auto text-zinc-600" />
                <p className="text-base font-semibold text-zinc-200">No Class Teaching Requests</p>
                <p className="text-xs text-zinc-500 max-w-md mx-auto">
                  Browse your school&apos;s available classes to request teaching privileges for specific batches.
                </p>
                <Link href="/teacher/classes">
                  <Button size="sm" variant="outline" className="mt-2 text-xs">
                    View School Classes <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Button>
                </Link>
              </GlassCard>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {myClassRequests.map((req) => (
                  <div
                    key={req.id}
                    className="p-5 rounded-2xl border border-zinc-800 bg-zinc-900/60 space-y-3"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h4 className="text-base font-bold text-white">{req.className}</h4>
                        <p className="text-xs text-zinc-400">Subject: {req.subject || "General"}</p>
                      </div>
                      <Badge
                        variant={
                          req.status === "APPROVED"
                            ? "success"
                            : req.status === "PENDING"
                            ? "warning"
                            : "destructive"
                        }
                      >
                        {req.status}
                      </Badge>
                    </div>

                    <div className="text-xs text-zinc-500 flex items-center gap-1.5 pt-2 border-t border-zinc-800">
                      <Clock size={13} />
                      Submitted on {new Date(req.requestedAt).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ─── APPROVAL MODAL WITH ROLL NUMBER ─── */}
        {approvingStudentReq && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-fade-in">
            <div className="w-full max-w-md rounded-2xl border border-zinc-700 bg-zinc-950 p-6 space-y-5 shadow-2xl">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-bold text-white">Approve Student Enrollment</h3>
                  <p className="text-xs text-zinc-400">
                    Assign a roll number for {approvingStudentReq.studentName} in {approvingStudentReq.className}.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setApprovingStudentReq(null)}
                  className="text-zinc-500 hover:text-white"
                >
                  ✕
                </button>
              </div>

              {actionError && (
                <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-300">
                  {actionError}
                </div>
              )}

              <div className="space-y-3">
                <label className="text-xs font-semibold text-zinc-300 block">Roll Number Assignment</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setRollNoMode("AUTO")}
                    className={`py-2 px-3 rounded-xl text-xs font-semibold border text-center transition-colors ${
                      rollNoMode === "AUTO"
                        ? "bg-indigo-600 border-indigo-500 text-white"
                        : "bg-zinc-900 border-zinc-800 text-zinc-400 hover:border-zinc-700"
                    }`}
                  >
                    Auto Generate Next
                  </button>
                  <button
                    type="button"
                    onClick={() => setRollNoMode("CUSTOM")}
                    className={`py-2 px-3 rounded-xl text-xs font-semibold border text-center transition-colors ${
                      rollNoMode === "CUSTOM"
                        ? "bg-indigo-600 border-indigo-500 text-white"
                        : "bg-zinc-900 border-zinc-800 text-zinc-400 hover:border-zinc-700"
                    }`}
                  >
                    Custom Roll Number
                  </button>
                </div>

                {rollNoMode === "CUSTOM" && (
                  <div className="pt-2">
                    <input
                      type="text"
                      placeholder="e.g. 101, A-12, 2026-001"
                      value={customRollNo}
                      onChange={(e) => setCustomRollNo(e.target.value)}
                      className="w-full px-3.5 py-2 rounded-xl border border-zinc-800 bg-zinc-900 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                )}
              </div>

              <div className="flex items-center gap-3 pt-3">
                <Button
                  className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
                  disabled={processingId !== null || (rollNoMode === "CUSTOM" && !customRollNo.trim())}
                  onClick={() => handleDecideStudent("APPROVED")}
                >
                  {processingId ? "Approving..." : "Confirm & Enroll"}
                </Button>
                <Button
                  variant="secondary"
                  className="w-full"
                  onClick={() => setApprovingStudentReq(null)}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
