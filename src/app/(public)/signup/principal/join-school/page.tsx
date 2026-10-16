"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { api } from "@/lib/axios";
import type { School } from "@/types/school";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/loading";
import { Building2, Search, X, Plus, RefreshCw } from "lucide-react";

export default function PrincipalJoinSchoolPage() {
  const router = useRouter();
  const [schools, setSchools] = useState<School[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedState, setSelectedState] = useState<string>("ALL");
  const [joiningSchoolId, setJoiningSchoolId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchSchools = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get<School[]>("/api/v1/schools");
      setSchools(data || []);
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
        await api.post("/api/v1/principals/", {
          experience: 0,
          schoolId,
        });
        router.push("/principal");
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

  const uniqueStates = useMemo(() => {
    const states = new Set<string>();
    schools.forEach((s) => {
      if (s.state) states.add(s.state.trim());
    });
    return Array.from(states).sort();
  }, [schools]);

  const filteredSchools = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    return schools.filter((school) => {
      const matchesSearch =
        !q ||
        school.name.toLowerCase().includes(q) ||
        school.schoolCode.toLowerCase().includes(q) ||
        school.city?.toLowerCase().includes(q) ||
        school.state?.toLowerCase().includes(q);

      const matchesState =
        selectedState === "ALL" || school.state === selectedState;

      return matchesSearch && matchesState;
    });
  }, [schools, searchQuery, selectedState]);

  return (
    <div className="page-shell">
      <div className="mx-auto max-w-6xl space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 rounded-3xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
              Join an Existing School as Principal
            </h1>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              Select your institution from the directory below to claim leadership and complete your principal setup.
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
              Register New School
            </Button>
          </div>
        </div>

        {error ? (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300">
            {error}
          </div>
        ) : null}

        {/* Search & Filter Bar */}
        {!loading && schools.length > 0 && (
          <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by school name, school code, city, or state..."
                className="w-full pl-11 pr-10 py-3 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
                  aria-label="Clear search"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>

            {uniqueStates.length > 0 && (
              <div className="flex items-center gap-2 shrink-0">
                <select
                  value={selectedState}
                  onChange={(e) => setSelectedState(e.target.value)}
                  className="px-3 py-3 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="ALL">All States ({schools.length})</option>
                  {uniqueStates.map((st) => (
                    <option key={st} value={st}>
                      {st}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        )}

        {/* Counter */}
        {!loading && schools.length > 0 && (
          <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 px-1">
            <span>
              Showing {filteredSchools.length} of {schools.length} institutions
            </span>
            {(searchQuery || selectedState !== "ALL") && (
              <button
                type="button"
                onClick={() => {
                  setSearchQuery("");
                  setSelectedState("ALL");
                }}
                className="text-indigo-600 dark:text-indigo-400 hover:underline font-medium"
              >
                Reset filters
              </button>
            )}
          </div>
        )}

        {loading ? (
          <div className="flex min-h-[220px] flex-col items-center justify-center gap-3 rounded-3xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
            <Spinner className="h-8 w-8 border-4 text-indigo-500" />
            <p className="text-xs text-zinc-400">Loading registered schools...</p>
          </div>
        ) : null}

        {!loading && schools.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-12 text-center space-y-4 dark:border-slate-800 dark:bg-slate-900/40">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Building2 className="h-8 w-8" />
            </div>
            <div className="space-y-1 max-w-md mx-auto">
              <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                No Schools Registered Yet
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                There are no existing schools in the system right now. You can create your own school right now to start managing your institute.
              </p>
            </div>
            <div className="pt-2">
              <Button
                onClick={() => router.push("/signup/principal/create-school")}
                className="bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                <Plus className="mr-2 h-4 w-4" />
                Register Your School Now
              </Button>
            </div>
          </div>
        ) : null}

        {!loading && schools.length > 0 && filteredSchools.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-10 text-center space-y-3 dark:border-slate-800 dark:bg-slate-900">
            <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
              No schools matched your search &quot;{searchQuery}&quot;.
            </p>
            <p className="text-xs text-slate-400">
              Try adjusting your query or register a new school if yours isn&apos;t listed yet.
            </p>
            <div className="pt-2 flex items-center justify-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSearchQuery("");
                  setSelectedState("ALL");
                }}
              >
                Clear Search
              </Button>
              <Button
                size="sm"
                onClick={() => router.push("/signup/principal/create-school")}
                className="bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                Register New School
              </Button>
            </div>
          </div>
        ) : null}

        {!loading && filteredSchools.length > 0 ? (
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
            {filteredSchools.map((school) => (
              <div
                key={school.id}
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900 flex flex-col justify-between"
              >
                <div className="space-y-1">
                  <div className="flex items-start justify-between gap-2">
                    <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                      {school.name}
                    </h2>
                    <span className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-semibold text-indigo-700 border border-indigo-200 dark:bg-indigo-950/40 dark:text-indigo-400 dark:border-indigo-800">
                      {school.type || "INSTITUTE"}
                    </span>
                  </div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {school.city ? `${school.city}, ` : ""}{school.state ? `${school.state}, ` : ""}{school.country || "India"}
                  </p>
                  <p className="text-xs uppercase tracking-wider text-slate-400 dark:text-slate-500 font-mono">
                    Code: {school.schoolCode}
                  </p>
                </div>

                <Button
                  className="mt-5 w-full bg-indigo-600 hover:bg-indigo-700 text-white"
                  disabled={joiningSchoolId === school.id}
                  onClick={() => handleJoin(school.id)}
                >
                  {joiningSchoolId === school.id
                    ? "Joining..."
                    : "Join as Principal"}
                </Button>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
