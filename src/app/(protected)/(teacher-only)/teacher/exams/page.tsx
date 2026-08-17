"use client";

import React, { useEffect, useMemo, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { Plus, BookOpen, Award, ClipboardList, CheckCircle2 } from "lucide-react";
import { PageHeader } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ExamCard } from "@/components/exam/ExamCard";
import { useExamStore } from "@/stores/useExamStore";

function TeacherExamsContent() {
  const { exams, loading, error, fetchExams } = useExamStore();
  const searchParams = useSearchParams();
  const router = useRouter();

  const tabParam = searchParams.get("tab");
  const activeTab: "all" | "published" | "results" =
    tabParam === "results" ? "results" : tabParam === "published" ? "published" : "all";

  useEffect(() => {
    fetchExams();
  }, [fetchExams]);

  const handleTabChange = (tab: "all" | "published" | "results") => {
    if (tab === "all") {
      router.push("/teacher/exams");
    } else {
      router.push(`/teacher/exams?tab=${tab}`);
    }
  };

  const publishedCount = useMemo(
    () => exams.filter((e) => e.isPublished).length,
    [exams]
  );
  const resultsCount = useMemo(
    () => exams.filter((e) => e.isPublished || e.isResultsReleased).length,
    [exams]
  );

  const displayedExams = useMemo(() => {
    if (activeTab === "published") {
      return exams.filter((e) => e.isPublished);
    }
    if (activeTab === "results") {
      return exams.filter((e) => e.isPublished || e.isResultsReleased);
    }
    return exams;
  }, [exams, activeTab]);

  return (
    <div className="page-shell">
      <div className="max-w-6xl mx-auto space-y-8 animate-fade-in-up">
        {/* Header */}
        <PageHeader
          overline="Assessments"
          title={activeTab === "results" ? "Exam Results & Leaderboards" : "My Exams"}
          subtitle={
            activeTab === "results"
              ? "Inspect student scoreboards, evaluate subjective submissions, and release grades."
              : "Manage your created exams, quizzes, and assignments."
          }
          actions={
            <Link href="/teacher/exams/create">
              <Button variant="primary">
                <Plus className="mr-2 h-4 w-4" /> Create Exam
              </Button>
            </Link>
          }
        />

        {/* Tabs Navigation */}
        <div className="flex items-center gap-2 border-b border-[var(--border-subtle)] pb-4 overflow-x-auto">
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
            <span>All Exams</span>
            <span className={`px-2 py-0.5 rounded-full text-xs ${activeTab === "all" ? "bg-white/20 text-white" : "bg-muted text-muted-foreground"}`}>
              {exams.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleTabChange("published")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              activeTab === "published"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-muted-foreground hover:text-foreground hover:bg-[var(--surface-2)]"
            }`}
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Published</span>
            <span className={`px-2 py-0.5 rounded-full text-xs ${activeTab === "published" ? "bg-white/20 text-white" : "bg-muted text-muted-foreground"}`}>
              {publishedCount}
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
            <span>Results & Scoreboards</span>
            <span className={`px-2 py-0.5 rounded-full text-xs ${activeTab === "results" ? "bg-white/20 text-white" : "bg-muted text-muted-foreground"}`}>
              {resultsCount}
            </span>
          </button>
        </div>

        {/* State Handling */}
        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-[250px] skeleton rounded-2xl" />
            ))}
          </div>
        )}

        {error && !loading && (
          <div className="p-4 rounded-xl bg-[var(--error-muted)] text-[var(--error)] border border-[var(--error)]/20">
            {error}
          </div>
        )}

        {!loading && !error && displayedExams.length === 0 && (
          <EmptyState
            icon={activeTab === "results" ? Award : BookOpen}
            title={activeTab === "results" ? "No Active Exam Results" : "No Exams Found"}
            description={
              activeTab === "results"
                ? "Publish exams and receive student submissions to view performance scoreboards."
                : "You haven't created any exams yet. Start by building your first assessment."
            }
            className="border border-[var(--border-subtle)] bg-[var(--surface-1)]"
            action={
              <Link href="/teacher/exams/create">
                <Button variant="primary">
                  <Plus className="mr-2 h-4 w-4" /> Create First Exam
                </Button>
              </Link>
            }
          />
        )}

        {/* Results Grid */}
        {!loading && !error && displayedExams.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {displayedExams.map((exam) => (
              <div key={exam.id} className="animate-fade-in stagger-1">
                <ExamCard exam={exam} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ExamsListPage() {
  return (
    <Suspense
      fallback={
        <div className="page-shell flex items-center justify-center min-h-[60vh]">
          <div className="w-10 h-10 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
        </div>
      }
    >
      <TeacherExamsContent />
    </Suspense>
  );
}
