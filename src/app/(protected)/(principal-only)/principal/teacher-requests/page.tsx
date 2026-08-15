"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  UserCheck,
  UserX,
  Clock,
  CheckCircle2,
  XCircle,
  Users,
  Building2,
  Calendar,
  BookOpen,
  ArrowLeft,
  Search,
} from "lucide-react";

import { PageHeader } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/loading";
import { api } from "@/lib/axios";

interface TeacherRequest {
  id: string;
  teacherId: string;
  teacherName: string;
  teacherEmail: string;
  classId: string;
  className: string;
  schoolId: string;
  subject?: string | null;
  status: "PENDING" | "APPROVED" | "REJECTED";
  requestedAt: string;
  decidedAt?: string | null;
  decidedBy?: string | null;
}

export default function PrincipalTeacherRequestsPage() {
  const router = useRouter();
  const [requests, setRequests] = useState<TeacherRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"ALL" | "PENDING" | "APPROVED" | "REJECTED">("PENDING");
  const [search, setSearch] = useState("");

  const fetchRequests = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Get current principal's school
      const schoolRes = await api.get<{ id: string }>("/api/v1/schools/my-school");
      const schoolId = schoolRes.data.id;

      // 2. Fetch teacher requests
      const res = await api.get<TeacherRequest[]>(
        `/api/v1/teacher-requests/school/${schoolId}`,
      );
      setRequests(res.data);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail;
      setError(detail ?? "Failed to load teacher class requests.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  const handleDecide = async (requestId: string, status: "APPROVED" | "REJECTED") => {
    setProcessingId(requestId);
    try {
      await api.patch(`/api/v1/teacher-requests/${requestId}`, { status });
      // Update local state
      setRequests((prev) =>
        prev.map((r) => (r.id === requestId ? { ...r, status } : r)),
      );
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail;
      alert(detail ?? "Failed to update request.");
    } finally {
      setProcessingId(null);
    }
  };

  const filtered = requests.filter((r) => {
    if (tab !== "ALL" && r.status !== tab) return false;
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      r.teacherName.toLowerCase().includes(q) ||
      r.teacherEmail.toLowerCase().includes(q) ||
      r.className.toLowerCase().includes(q)
    );
  });

  const pendingCount = requests.filter((r) => r.status === "PENDING").length;

  return (
    <div className="page-shell">
      <div className="max-w-6xl mx-auto space-y-8 animate-fade-in-up">
        <PageHeader
          overline="School Administration"
          title="Teacher Class Requests"
          subtitle="Review and decide requests submitted by teachers to join and instruct classes in your school."
          actions={
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push("/principal")}
              className="flex items-center gap-2"
            >
              <ArrowLeft size={16} /> Back to Dashboard
            </Button>
          }
        />

        {/* Tab & Search Bar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
          <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-xl gap-1">
            <button
              onClick={() => setTab("PENDING")}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 ${
                tab === "PENDING"
                  ? "bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm"
                  : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
              }`}
            >
              <Clock size={15} />
              Pending
              {pendingCount > 0 && (
                <span className="px-2 py-0.5 text-xs rounded-full bg-amber-500 text-white font-bold">
                  {pendingCount}
                </span>
              )}
            </button>
            <button
              onClick={() => setTab("APPROVED")}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 ${
                tab === "APPROVED"
                  ? "bg-white dark:bg-slate-900 text-emerald-600 dark:text-emerald-400 shadow-sm"
                  : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
              }`}
            >
              <CheckCircle2 size={15} />
              Approved
            </button>
            <button
              onClick={() => setTab("REJECTED")}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 ${
                tab === "REJECTED"
                  ? "bg-white dark:bg-slate-900 text-red-600 dark:text-red-400 shadow-sm"
                  : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
              }`}
            >
              <XCircle size={15} />
              Rejected
            </button>
            <button
              onClick={() => setTab("ALL")}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
                tab === "ALL"
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
              placeholder="Search teacher or class..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        {/* Requests List */}
        {loading ? (
          <div className="py-20 text-center">
            <Spinner className="h-8 w-8 text-indigo-600 mx-auto" />
            <p className="mt-2 text-sm text-slate-500">Loading requests...</p>
          </div>
        ) : error ? (
          <GlassCard padding="lg" className="text-center py-12 space-y-3">
            <p className="text-red-500 font-bold">{error}</p>
            <Button onClick={fetchRequests} variant="outline" size="sm">
              Retry
            </Button>
          </GlassCard>
        ) : filtered.length === 0 ? (
          <GlassCard padding="lg" className="text-center py-16 space-y-3">
            <Users size={40} className="mx-auto text-slate-300 dark:text-slate-600" />
            <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-300">
              No Requests in this tab
            </h3>
            <p className="text-sm text-slate-500 max-w-sm mx-auto">
              There are currently no teacher class join requests matching your selected filter.
            </p>
          </GlassCard>
        ) : (
          <div className="grid gap-4">
            {filtered.map((req) => (
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

                {/* Actions */}
                {req.status === "PENDING" && (
                  <div className="flex items-center gap-2 self-end md:self-center">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={processingId === req.id}
                      onClick={() => handleDecide(req.id, "REJECTED")}
                      className="border-red-200 text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30"
                    >
                      <UserX size={15} className="mr-1.5" />
                      Reject
                    </Button>
                    <Button
                      size="sm"
                      variant="primary"
                      disabled={processingId === req.id}
                      onClick={() => handleDecide(req.id, "APPROVED")}
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
        )}
      </div>
    </div>
  );
}
