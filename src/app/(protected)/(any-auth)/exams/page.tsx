"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/axios";
import { ExamPublicCard } from "@/components/exam/ExamPublicCard";
import { ExamSearchFilters } from "@/components/exam/ExamSearchFilters";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { Search, Compass } from "lucide-react";
import type { Exam } from "@/types";
import { useAuthStore } from "@/stores/useAuthStore";

export default function ExamsDiscoveryPage() {
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState(true);
  const user = useAuthStore((state) => state.user);
  const isStudent = user?.role === "STUDENT";

  const [filters, setFilters] = useState({
    name: "",
    type: "",
    teacherName: "",
    schoolName: "",
    subject: "",
  });

  const fetchExams = async () => {
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
        `/api/v1/exams/public/?${params.toString()}`
      );

      setExams(response.data);
    } catch (error) {
      console.error("Failed to fetch public exams:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(fetchExams, 400);
    return () => clearTimeout(timer);
  }, [filters]);

  const hasActiveFilters = Object.values(filters).some(Boolean);

  return (
    <div className="container mx-auto py-8 px-4">
      <PageHeader
        title="Public Assessments"
        description="Discover and view detailed profiles of published examinations from schools and teachers worldwide."
        className="mb-10"
        actions={
          <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-[var(--accent)]/10 text-[var(--accent)] border border-[var(--accent)]/20 text-sm font-medium">
            <Compass className="w-4 h-4" />
            <span>Discovery Hub</span>
          </div>
        }
      />

      {/* Active filters indicator */}
      {hasActiveFilters && (
        <div className="flex items-center gap-2 mb-6 text-sm text-muted-foreground">
          <Search className="w-4 h-4" />
          <span>Showing results based on applied filters</span>
        </div>
      )}

      <div className="flex flex-col lg:grid lg:grid-cols-4 gap-8">
        {/* Sidebar */}
        <aside className="lg:col-span-1">
          <ExamSearchFilters
            filters={filters}
            setFilters={setFilters}
            onClear={() =>
              setFilters({
                name: "",
                type: "",
                teacherName: "",
                schoolName: "",
                subject: "",
              })
            }
          />
        </aside>

        {/* Main content */}
        <main className="lg:col-span-3">
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-[280px] w-full rounded-2xl" />
              ))}
            </div>
          ) : exams.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {exams.map((exam) => (
                <ExamPublicCard key={exam.id} exam={exam} isStudent={isStudent} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={<Search className="w-12 h-12" />}
              title="No Exams Found"
              description={
                hasActiveFilters
                  ? "No results match your filters. Try adjusting them."
                  : "No public exams available yet."
              }
            />
          )}
        </main>
      </div>
    </div>
  );
}