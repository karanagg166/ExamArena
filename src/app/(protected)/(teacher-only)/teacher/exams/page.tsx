"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { Plus, BookOpen } from "lucide-react";
import { PageHeader } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ExamCard } from "@/components/exam/ExamCard";
import { useExamStore } from "@/stores/useExamStore";

export default function ExamsListPage() {
  const { exams, loading, error, fetchExams } = useExamStore();

  useEffect(() => {
    fetchExams();
  }, [fetchExams]);

  return (
    <div className="page-shell">
      <div className="max-w-6xl mx-auto space-y-8 animate-fade-in-up">
        {/* Header */}
        <PageHeader
          overline="Assessments"
          title="My Exams"
          subtitle="Manage your created exams, quizzes, and assignments."
          actions={
            <Link href="/teacher/exams/create">
              <Button variant="primary">
                <Plus className="mr-2 h-4 w-4" /> Create Exam
              </Button>
            </Link>
          }
        />

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

        {!loading && !error && exams.length === 0 && (
          <EmptyState
            icon={BookOpen}
            title="No Exams Found"
            description="You haven't created any exams yet. Start by building your first assessment."
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
        {!loading && !error && exams.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {exams.map((exam) => (
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
