"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { api } from "@/lib/axios";
import type { School } from "@/types/school";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/loading";

type JoinPayload = {
  schoolId: string;
};

export default function TeacherJoinSchoolPage() {
  const router = useRouter();
  const [schools, setSchools] = useState<School[]>([]);
  const [loading, setLoading] = useState(true);
  const [joiningSchoolId, setJoiningSchoolId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchSchools = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get<School[]>("/api/v1/schools");
      setSchools(data);
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
  }, []);

  useEffect(() => {
    fetchSchools();
  }, [fetchSchools]);

  const handleJoin = useCallback(
    async (schoolId: string) => {
      setJoiningSchoolId(schoolId);
      setError(null);
      try {
        const payload: JoinPayload = { schoolId };
        await api.post("/api/v1/teachers/me/join-school", payload);
        router.push("/teacher/school");
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
        setJoiningSchoolId(null);
      }
    },
    [router],
  );

  return (
    <div className="page-shell">
      <div className="mx-auto max-w-6xl space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
        <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
            Join a School
          </h1>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
            Select a school from the list to connect your teacher profile.
          </p>
        </div>

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
            {schools.map((school) => (
              <div
                key={school.id}
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
              >
                <div className="space-y-1">
                  <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                    {school.name}
                  </h2>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {school.city}, {school.state}, {school.country}
                  </p>
                  <p className="text-xs uppercase tracking-wider text-slate-400 dark:text-slate-500">
                    Code: {school.schoolCode}
                  </p>
                </div>

                <Button
                  className="mt-4 w-full"
                  disabled={joiningSchoolId === school.id}
                  onClick={() => handleJoin(school.id)}
                >
                  {joiningSchoolId === school.id ? "Joining..." : "Join School"}
                </Button>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
