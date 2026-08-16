"use client";

import React, { useState, useMemo, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Save, Building2 } from "lucide-react";
import Link from "next/link";

import { PageHeader } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";
import { FormMessage } from "@/components/ui/form-message";
import { ExamForm } from "@/components/exam/ExamForm";
import { QuestionList } from "@/components/question/QuestionList";
import { Spinner } from "@/components/ui/loading";
import { api } from "@/lib/axios";
import { getErrorMessage } from "@/lib/error";
import { validateExam, computeMaxMarks } from "@/lib/exam-validation";
import { useSchoolStore } from "@/stores";
import type { ExamCreate } from "@/types";

export default function CreateExamPage() {
  const router = useRouter();
  const { school, loading: schoolLoading, hasFetched, fetchSchool } = useSchoolStore();
  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  useEffect(() => {
    if (!hasFetched) fetchSchool();
  }, [hasFetched, fetchSchool]);

  const [exam, setExam] = useState<ExamCreate>({
    name: "",
    examCode: "",
    accessPassword: "",
    description: "",
    scheduledAt: "",
    duration: 60,
    type: "MIDTERM",
    maxMarks: 0,
    isPublished: false,
    isPublic: true,
    negativeMarking: false,
    negativeMarks: 0,
    questions: [],
  });

  // ── Auto-compute maxMarks from questions ──────────────────────────────────
  const maxMarks = useMemo(
    () => computeMaxMarks(exam.questions ?? []),
    [exam.questions]
  );

  // ── Submit ────────────────────────────────────────────────────────────────
  const handleCreate = async () => {
    setErrorText(null);

    const validationError = validateExam(exam);
    if (validationError) return setErrorText(validationError);

    setLoading(true);
    try {
      await api.post("/api/v1/exams/", { ...exam, maxMarks });
      router.push("/teacher/exams");
    } catch (err: unknown) {
      setErrorText(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (schoolLoading) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <Spinner className="h-10 w-10 text-indigo-500 border-4" />
      </div>
    );
  }

  if (!school) {
    return (
      <div className="flex min-h-[70vh] flex-col items-center justify-center p-6 text-center">
        <div className="max-w-lg rounded-2xl border border-zinc-800 bg-zinc-950/60 p-8 shadow-xl space-y-4">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-400">
            <Building2 className="h-7 w-7" />
          </div>
          <h2 className="text-2xl font-bold text-white">School Affiliation Required</h2>
          <p className="text-sm text-zinc-400 leading-relaxed">
            You must first join and be approved by a School before you can create and publish exams. Once your school affiliation is confirmed by the Principal, you can create exams for your assigned classes.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
            <Button onClick={() => router.push("/teacher/school/join")}>
              Join a School →
            </Button>
            <Button variant="secondary" onClick={() => router.push("/teacher/requests?tab=status")}>
              View Request Status
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-shell">
      <div className="max-w-4xl mx-auto space-y-8 animate-fade-in-up">

        <PageHeader
          overline="Exam Builder"
          title="Create New Exam"
          subtitle="Configure exam details and add your questions in one place."
          actions={
            <div className="flex gap-3">
              <Link href="/teacher/exams">
                <Button variant="ghost" className="hidden sm:flex">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Cancel
                </Button>
              </Link>
              <Button variant="primary" onClick={handleCreate} disabled={loading}>
                <Save className="mr-2 h-4 w-4" />
                {loading ? "Creating..." : "Save Exam"}
              </Button>
            </div>
          }
        />

        {errorText && <FormMessage type="error" message={errorText} />}

        {/* ── Total Marks Badge ─────────────────────────────────────────── */}
        {maxMarks > 0 && (
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            <span>Total Marks:</span>
            <span className="font-semibold text-white bg-indigo-600/20 border border-indigo-500/30 px-2 py-0.5 rounded-md">
              {maxMarks}
            </span>
          </div>
        )}

        <ExamForm
          exam={{ ...exam, maxMarks }}
          onChange={(updates) => setExam((prev) => ({ ...prev, ...updates }))}
        />

        <hr className="divider" />

        <QuestionList
          questions={exam.questions ?? []}
          onChange={(questions) => setExam((prev) => ({ ...prev, questions }))}
        />

        {/* ── Sticky Mobile Footer ──────────────────────────────────────── */}
        <div className="sm:hidden fixed bottom-0 left-0 right-0 p-4 bg-[var(--background)] border-t border-[var(--border-subtle)] z-50">
          <Button
            variant="primary"
            className="w-full shadow-glow"
            onClick={handleCreate}
            disabled={loading}
          >
            {loading ? "Creating..." : "Save Complete Exam"}
          </Button>
        </div>

      </div>
    </div>
  );
}