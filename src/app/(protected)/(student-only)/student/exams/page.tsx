"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/axios";
import { ExamPublicCard } from "@/components/exam/ExamPublicCard";
import { ExamSearchFilters } from "@/components/exam/ExamSearchFilters";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { Search, GraduationCap } from "lucide-react";
import type { Exam } from "@/types";

interface StudentExam extends Exam {
  studentStatus: string;
  attemptId: string | null;
}

export default function StudentExamsDashboardPage() {
  const [exams, setExams] = useState<StudentExam[]>([]);
  const [loading, setLoading] = useState(true);

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
        `/api/v1/exams/student/?${params.toString()}`
      );
      setExams(response.data);
    } catch (error) {
      console.error("Failed to fetch student exams:", error);
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
        title="My Assessments"
        description="Discover and take exams published by your school and teachers."
        className="mb-10"
        actions={
          <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-[var(--accent)]/10 text-[var(--accent)] border border-[var(--accent)]/20 text-sm font-medium">
            <GraduationCap className="w-4 h-4" />
            <span>Student Portal</span>
          </div>
        }
      />

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
          ) : exams.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {exams.map((exam) => (
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
              icon={<GraduationCap className="w-12 h-12" />}
              title="No Exams Found"
              description={
                hasActiveFilters
                  ? "No results match your filters. Try adjusting them."
                  : "No exams have been assigned to your school yet."
              }
            />
          )}
        </main>
      </div>
    </div>
  );
}
