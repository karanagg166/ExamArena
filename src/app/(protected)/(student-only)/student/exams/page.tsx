"use client";

import React, { useCallback, useEffect, useMemo, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { api } from "@/lib/axios";
import { ExamPublicCard } from "@/components/exam/ExamPublicCard";
import { ExamSearchFilters } from "@/components/exam/ExamSearchFilters";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { Search, GraduationCap, Award, ClipboardList, Clock } from "lucide-react";
import type { Exam } from "@/types";

interface StudentExam extends Exam {
  studentStatus: string;
  attemptId: string | null;
}

function StudentExamsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const tabParam = searchParams.get("tab");
  const activeTab: "all" | "pending" | "results" =
    tabParam === "results" ? "results" : tabParam === "pending" ? "pending" : "all";

  const [exams, setExams] = useState<StudentExam[]>([]);
  const [loading, setLoading] = useState(true);

  const [filters, setFilters] = useState({
    name: "",
    code: "",
    type: "",
    teacherName: "",
    schoolName: "",
    subject: "",
  });

  const fetchExams = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();

      Object.entries(filters).forEach(([key, value]) => {
        if (!value) return;
        const apiKey =
          key === "teacherName"
            ? "teacher_name"
            : key === "schoolName"
              ? "school_name"
              : key;
        params.append(apiKey, value);
      });

      const response = await api.get(
        `/api/v1/exams/student/?${params.toString()}`
      );
      setExams(response.data);
    } catch (error) {
      console.error("Failed to fetch student exams:", error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    const timer = setTimeout(fetchExams, 400);
    return () => clearTimeout(timer);
  }, [fetchExams]);

  const handleTabChange = (tab: "all" | "pending" | "results") => {
    if (tab === "all") {
      router.push("/student/exams");
    } else {
      router.push(`/student/exams?tab=${tab}`);
    }
  };

  const pendingCount = useMemo(
    () => exams.filter((e) => e.studentStatus === "NOT_ATTEMPTED").length,
    [exams]
  );
  const resultsCount = useMemo(
    () =>
      exams.filter(
        (e) => e.studentStatus !== "NOT_ATTEMPTED" || e.isResultsReleased
      ).length,
    [exams]
  );

  const displayedExams = useMemo(() => {
    if (activeTab === "pending") {
      return exams.filter((e) => e.studentStatus === "NOT_ATTEMPTED");
    }
    if (activeTab === "results") {
      return exams.filter(
        (e) => e.studentStatus !== "NOT_ATTEMPTED" || e.isResultsReleased
      );
    }
    return exams;
  }, [exams, activeTab]);

  const hasActiveFilters = Object.values(filters).some(Boolean);

  return (
    <div className="container mx-auto py-8 px-4">
      <PageHeader
        title={activeTab === "results" ? "Exam Results & Performance" : "My Assessments"}
        description={
          activeTab === "results"
            ? "Review your completed exams, evaluated scores, rank standing, and detailed answer explanations."
            : "Discover and take exams published by your school and teachers."
        }
        className="mb-8"
        actions={
          <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-[var(--accent)]/10 text-[var(--accent)] border border-[var(--accent)]/20 text-sm font-medium">
            <GraduationCap className="w-4 h-4" />
            <span>Student Portal</span>
          </div>
        }
      />

      {/* Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-[var(--border-subtle)] pb-4 mb-8 overflow-x-auto">
        <button
          type="button"
          onClick={() => handleTabChange("all")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
            activeTab === "all"
              ? "bg-indigo-600 text-white shadow-sm"
              : "text-muted-foreground hover:text-foreground hover:bg-[var(--surface-2)]"
          }`}
        >
          <ClipboardList className="w-4 h-4" />
          <span>All Assessments</span>
          <span className={`px-2 py-0.5 rounded-full text-xs ${activeTab === "all" ? "bg-white/20 text-white" : "bg-muted text-muted-foreground"}`}>
            {exams.length}
          </span>
        </button>

        <button
          type="button"
          onClick={() => handleTabChange("pending")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
            activeTab === "pending"
              ? "bg-indigo-600 text-white shadow-sm"
              : "text-muted-foreground hover:text-foreground hover:bg-[var(--surface-2)]"
          }`}
        >
          <Clock className="w-4 h-4" />
          <span>To Take</span>
          <span className={`px-2 py-0.5 rounded-full text-xs ${activeTab === "pending" ? "bg-white/20 text-white" : "bg-muted text-muted-foreground"}`}>
            {pendingCount}
          </span>
        </button>

        <button
          type="button"
          onClick={() => handleTabChange("results")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
            activeTab === "results"
              ? "bg-indigo-600 text-white shadow-sm"
              : "text-muted-foreground hover:text-foreground hover:bg-[var(--surface-2)]"
          }`}
        >
          <Award className="w-4 h-4" />
          <span>Results & Scores</span>
          <span className={`px-2 py-0.5 rounded-full text-xs ${activeTab === "results" ? "bg-white/20 text-white" : "bg-muted text-muted-foreground"}`}>
            {resultsCount}
          </span>
        </button>
      </div>

      {hasActiveFilters && (
        <div className="flex items-center gap-2 mb-6 text-sm text-muted-foreground">
          <Search className="w-4 h-4" />
          <span>Showing results based on applied filters</span>
        </div>
      )}

      <div className="flex flex-col lg:grid lg:grid-cols-4 gap-8">
        <aside className="lg:col-span-1">
          <ExamSearchFilters
            filters={filters}
            setFilters={setFilters}
            onClear={() =>
              setFilters({
                name: "",
                code: "",
                type: "",
                teacherName: "",
                schoolName: "",
                subject: "",
              })
            }
          />
        </aside>

        <main className="lg:col-span-3">
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-[280px] w-full rounded-2xl" />
              ))}
            </div>
          ) : displayedExams.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {displayedExams.map((exam) => (
                <div key={exam.id} className="relative">
                  <ExamPublicCard exam={exam} isStudent={true} />
                  {exam.studentStatus !== "NOT_ATTEMPTED" && (
                    <div className="absolute top-4 right-4 z-10">
                      <span className={`px-2 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full border ${
                        exam.studentStatus === "IN_PROGRESS" 
                          ? "bg-amber-500/10 text-amber-500 border-amber-500/20" 
                          : "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                      }`}>
                        {exam.studentStatus.replace("_", " ")}
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={activeTab === "results" ? <Award className="w-12 h-12" /> : <GraduationCap className="w-12 h-12" />}
              title={activeTab === "results" ? "No Exam Results Yet" : "No Exams Found"}
              description={
                hasActiveFilters
                  ? "No results match your filters. Try adjusting them."
                  : activeTab === "results"
                  ? "You haven't completed any assessments or released results yet."
                  : "No exams have been assigned to your school yet."
              }
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default function StudentExamsDashboardPage() {
  return (
    <Suspense fallback={
      <div className="container mx-auto py-12 px-4 flex items-center justify-center min-h-[60vh]">
        <div className="w-10 h-10 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
      </div>
    }>
      <StudentExamsContent />
    </Suspense>
  );
}
