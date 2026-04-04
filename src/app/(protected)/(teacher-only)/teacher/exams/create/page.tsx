"use client";

import React, { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Save } from "lucide-react";
import Link from "next/link";
import type { AxiosError } from "axios";

import { PageHeader } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";
import { FormMessage } from "@/components/ui/form-message";
import { ExamForm } from "@/components/exam/ExamForm";
import { QuestionList } from "@/components/question/QuestionList";
import { api } from "@/lib/axios";
import { getErrorMessage } from "@/lib/error";
import type { ExamCreate } from "@/types";

export default function CreateExamPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  const [exam, setExam] = useState<ExamCreate>({
    name: "",
    description: "",
    scheduledAt: "",
    duration: 60,
    type: "MIDTERM",
    maxMarks: 0,
    isPublished: false,
    questions: [],
  });

  // ── Auto-compute maxMarks from questions ──────────────────────────────────
  const maxMarks = useMemo(
    () => (exam.questions ?? []).reduce((sum, q) => sum + (q.marks ?? 0), 0),
    [exam.questions]
  );

  // ── Validation ────────────────────────────────────────────────────────────
  const validate = (): string | null => {
    if (!exam.name.trim()) return "Exam title is required.";
    if (!exam.description.trim()) return "Description is required.";
    if (!exam.scheduledAt) return "Scheduled date is required.";
    if (exam.duration < 5) return "Duration must be at least 5 minutes.";
    if ((exam.questions ?? []).length === 0) return "Add at least one question.";

    for (const q of exam.questions ?? []) {
      if (!q.text.trim()) return "All questions must have a prompt.";
      if (!q.section?.trim()) return "All questions must have a section (e.g. Physics).";
      if (!q.marks || q.marks < 1)
        return `Question ${q.questionNumber} must have marks greater than 0.`;
      if (
        q.questionType === "MULTIPLE_CHOICE" ||
        q.questionType === "TRUE_FALSE"
      ) {
        if (!q.options?.some((o) => o.isCorrect))
          return `Question ${q.questionNumber} must have a correct option selected.`;
      }
    }

    return null;
  };

  // ── Submit ────────────────────────────────────────────────────────────────
  const handleCreate = async () => {
    setErrorText(null);

    const validationError = validate();
    if (validationError) return setErrorText(validationError);

    setLoading(true);
    try {
      console.log(exam);
      await api.post("/api/v1/exams/", { ...exam, maxMarks });
      router.push("/teacher/exams");
    } catch (err: unknown) {
      setErrorText(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

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
          exam={exam}
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