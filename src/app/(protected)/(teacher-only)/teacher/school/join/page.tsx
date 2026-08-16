"use client";

import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { api } from "@/lib/axios";
import type { School } from "@/types/school";
import { useTeacherRequestStore } from "@/stores";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/loading";

export default function TeacherJoinSchoolPage() {
  const [schools, setSchools] = useState<School[]>([]);
  const [loading, setLoading] = useState(true);
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
      const [{ data: schoolsData }] = await Promise.all([
        api.get<School[]>("/api/v1/schools"),
        fetchMySchoolRequests(),
      ]);
      setSchools(schoolsData);
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        setError(
          typeof detail === "string"
            ? detail
            : (err.message ?? "Something went wrong"),
        );
      } else {
        setError("Something went wrong");
      }
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

  return (
    <div className="page-shell">
      <div className="mx-auto max-w-6xl space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
        <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
            Request to Join a School
          </h1>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
            Select a school to send a join request. Once the Principal approves, you will be enrolled as faculty.
          </p>
        </div>

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
          <div className="flex min-h-[220px] items-center justify-center rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
            <Spinner className="h-8 w-8 border-4" />
          </div>
        ) : null}

        {!loading && schools.length === 0 ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center dark:border-slate-800 dark:bg-slate-900">
            <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              No schools found
            </p>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Ask a principal to create a school first.
            </p>
          </div>
        ) : null}

        {!loading && schools.length > 0 ? (
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
            {schools.map((school) => {
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

