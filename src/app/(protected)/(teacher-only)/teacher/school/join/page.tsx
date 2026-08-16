"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/axios";
import type { School } from "@/types/school";
import { useTeacherRequestStore } from "@/stores";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/loading";
import { Building2, Plus, RefreshCw, Search } from "lucide-react";

export default function TeacherJoinSchoolPage() {
  const router = useRouter();
  const [schools, setSchools] = useState<School[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [submittingSchoolId, setSubmittingSchoolId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const {
    mySchoolRequests,
    fetchMySchoolRequests,
    requestToJoinSchool,
  } = useTeacherRequestStore();

  const fetchSchools = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [schoolsResult] = await Promise.allSettled([
        api.get<School[]>("/api/v1/schools"),
        fetchMySchoolRequests(),
      ]);

      if (schoolsResult.status === "fulfilled") {
        setSchools(schoolsResult.value.data || []);
      } else {
        setSchools([]);
      }
    } catch {
      setSchools([]);
    } finally {
      setLoading(false);
    }
  }, [fetchMySchoolRequests]);

  useEffect(() => {
    fetchSchools();
  }, [fetchSchools]);

  const handleRequestJoin = useCallback(
    async (schoolId: string) => {
      setSubmittingSchoolId(schoolId);
      setError(null);
      setSuccessMsg(null);
      const res = await requestToJoinSchool(schoolId);
      if (res.success) {
        setSuccessMsg(
          "Your join request was submitted successfully! The Principal will review and accept your request."
        );
      } else {
        setError(res.error || "Failed to submit join request");
      }
      setSubmittingSchoolId(null);
    },
    [requestToJoinSchool],
  );

  const filteredSchools = schools.filter((s) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      s.name.toLowerCase().includes(q) ||
      s.schoolCode.toLowerCase().includes(q) ||
      s.city?.toLowerCase().includes(q) ||
      s.state?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="page-shell">
      <div className="mx-auto max-w-6xl space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 rounded-3xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
              Request to Join a School
            </h1>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              Select a school to send a faculty join request for Principal review.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={fetchSchools}
              disabled={loading}
              className="text-xs"
            >
              <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button
              size="sm"
              onClick={() => router.push("/signup/principal/create-school")}
              className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs"
            >
              <Plus className="mr-1.5 h-3.5 w-3.5" />
              Create School as Principal
            </Button>
          </div>
        </div>

        {/* Search Bar */}
        {schools.length > 0 && (
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search schools by name, code, or city..."
              className="w-full pl-11 pr-4 py-3 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        )}

        {successMsg ? (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300">
            {successMsg}
          </div>
        ) : null}

        {error ? (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300">
            {error}
          </div>
        ) : null}

        {loading ? (
          <div className="flex min-h-[260px] flex-col items-center justify-center gap-3 rounded-3xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
            <Spinner className="h-8 w-8 border-4 text-indigo-500" />
            <p className="text-xs text-zinc-400">Loading available schools...</p>
          </div>
        ) : null}

        {!loading && schools.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900/40 p-12 text-center space-y-4">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Building2 className="h-8 w-8" />
            </div>
            <div className="space-y-1 max-w-md mx-auto">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                No Schools Registered Yet
              </h3>
              <p className="text-sm text-slate-500 dark:text-zinc-400">
                There are currently no active schools in the system. You can create a new school right now by setting up a principal account, or ask your administrator to register.
              </p>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <Button
                onClick={() => router.push("/signup/principal/create-school")}
                className="bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                <Plus className="mr-2 h-4 w-4" />
                Create School as Principal
              </Button>
              <Button variant="outline" onClick={fetchSchools}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh
              </Button>
            </div>
          </div>
        ) : null}

        {!loading && schools.length > 0 && filteredSchools.length === 0 ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center dark:border-slate-800 dark:bg-slate-900">
            <p className="text-sm text-slate-500 dark:text-slate-400">
              No schools match &quot;{searchQuery}&quot;. Try a different search term.
            </p>
          </div>
        ) : null}

        {!loading && filteredSchools.length > 0 ? (
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
            {filteredSchools.map((school) => {
              const existingReq = mySchoolRequests.find(
                (r) => r.schoolId === school.id
              );
              const isPending = existingReq?.status === "PENDING";
              const isApproved = existingReq?.status === "APPROVED";
              const isRejected = existingReq?.status === "REJECTED";

              return (
                <div
                  key={school.id}
                  className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900 flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                        {school.name}
                      </h2>
                      {isPending && (
                        <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700 border border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800">
                          Pending Approval
                        </span>
                      )}
                      {isApproved && (
                        <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800">
                          Approved
                        </span>
                      )}
                      {isRejected && (
                        <span className="rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-semibold text-rose-700 border border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-800">
                          Declined
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      {school.city}, {school.state}, {school.country}
                    </p>
                    <p className="text-xs uppercase tracking-wider text-slate-400 dark:text-slate-500">
                      Code: {school.schoolCode}
                    </p>
                  </div>

                  <div className="mt-5">
                    {isPending ? (
                      <Button className="w-full" disabled variant="outline">
                        Request Pending Approval
                      </Button>
                    ) : isApproved ? (
                      <Button
                        className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
                        onClick={() => window.location.assign("/teacher/school")}
                      >
                        Go to School Portal
                      </Button>
                    ) : (
                      <Button
                        className="w-full"
                        disabled={submittingSchoolId === school.id}
                        onClick={() => handleRequestJoin(school.id)}
                      >
                        {submittingSchoolId === school.id
                          ? "Submitting..."
                          : isRejected
                          ? "Re-apply to Join"
                          : "Request to Join"}
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : null}
      </div>
    </div>
  );
}


