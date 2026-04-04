"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, Save } from "lucide-react";
import Link from "next/link";

import { PageHeader } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";
import { FormMessage } from "@/components/ui/form-message";
import { GlassCard } from "@/components/ui/glass-card";
import { ExamForm } from "@/components/exam/ExamForm";
import { QuestionList } from "@/components/question/QuestionList";
import { api } from "@/lib/axios";
import { getErrorMessage } from "@/lib/error";
import type { ExamUpdate, Exam } from "@/types";

export default function EditExamPage() {
  const { examId } = useParams();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [errorText, setErrorText] = useState<string | null>(null);

  const [exam, setExam] = useState<ExamUpdate>({
    id: examId as string,
    name: "",
    description: "",
    scheduledAt: "",
    duration: 60,
    type: "MIDTERM",
    maxMarks: 0,
    isPublished: false,
    questions: [],
  });

  // ── Fetch Initial Data ───────────────────────────────────────────────────
  useEffect(() => {
    const fetchExam = async () => {
      try {
        const response = await api.get(`/api/v1/exams/${examId}`);
        const data = response.data as Exam;

        setExam({
          id: data.id,
          name: data.name,
          description: data.description,
          scheduledAt: data.scheduledAt,
          duration: data.duration,
          type: data.type,
          maxMarks: data.maxMarks,
          isPublished: data.isPublished,
          instructions: data.instructions,
          subject: data.subject,
          questions: (data.questions ?? []).map((q) => ({
            ...q,
            options: q.options?.map((o) => ({ ...o })),
          })),
        });
      } catch (err: unknown) {
        setErrorText(getErrorMessage(err));
      } finally {
        setFetching(false);
      }
    };

    if (examId) fetchExam();
  }, [examId]);

  // ── Auto-compute maxMarks from questions ─────────────────────────────────
  const computedMaxMarks = useMemo(
    () => (exam.questions ?? []).reduce((sum, q) => sum + (q.marks ?? 0), 0),
    [exam.questions]
  );

  // ── Validation ────────────────────────────────────────────────────────────
  const validate = (): string | null => {
    if (!exam.name?.trim()) return "Exam title is required.";
    if (!exam.description?.trim()) return "Description is required.";
    if (!exam.scheduledAt) return "Scheduled date is required.";
    if ((exam.duration || 0) < 5) return "Duration must be at least 5 minutes.";
    if ((exam.questions ?? []).length === 0) return "Add at least one question.";

    for (const q of exam.questions ?? []) {
      if (!q.text.trim()) return "All questions must have a prompt.";
      if (!q.section?.trim()) return "All questions must have a section (e.g. Physics).";
      if (!q.marks || q.marks < 1)
        return `Question ${q.questionNumber} must have marks greater than 0.`;
      if (
        q.questionType === "MULTIPLE_CHOICE" ||
        q.questionType === "TRUE_FALSE" ||
        q.questionType === "MULTIPLE_SELECT"
      ) {
        if (!q.options?.some((o) => o.isCorrect))
          return `Question ${q.questionNumber} must have a correct option selected.`;
      }
    }

    return null;
  };

  // ── Submit ────────────────────────────────────────────────────────────────
  const handleUpdate = async () => {
    setErrorText(null);

    const validationError = validate();
    if (validationError) return setErrorText(validationError);

    setLoading(true);
    try {
      await api.patch(`/api/v1/exams/${examId}`, {
        ...exam,
        maxMarks: computedMaxMarks,
      });
      router.push(`/teacher/exams/${examId}`);
    } catch (err: unknown) {
      setErrorText(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  // ── Loading State ─────────────────────────────────────────────────────────
  if (fetching) {
    return (
      <div className="page-shell flex items-center justify-center min-h-[60vh]">
        <div className="w-8 h-8 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="page-shell">
      <div className="max-w-4xl mx-auto space-y-8 animate-fade-in-up">

        {/* ── Header ───────────────────────────────────────────────────── */}
        <PageHeader
          overline="Exam Editor"
          title="Edit Your Exam"
          subtitle="Modify your paper details, adjust marks, or add new questions."
          actions={
            <div className="flex gap-3">
              <Link href={`/teacher/exams/${examId}`}>
                <Button variant="ghost" className="hidden sm:flex">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Discard Changes
                </Button>
              </Link>
              <Button variant="primary" onClick={handleUpdate} disabled={loading}>
                <Save className="mr-2 h-4 w-4" />
                {loading ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          }
        />

        {/* ── Error Message ─────────────────────────────────────────────── */}
        {errorText && (
          <FormMessage type="error" message={errorText} />         // ✅ using FormMessage
        )}

        {/* ── Total Marks Badge ─────────────────────────────────────────── */}
        {computedMaxMarks > 0 && (
          <GlassCard className="flex items-center gap-3 px-4 py-3">
            <span className="text-sm text-zinc-400">Total Marks:</span>
            <span className="font-semibold text-white bg-indigo-600/20 border border-indigo-500/30 px-2 py-0.5 rounded-md">
              {computedMaxMarks}
            </span>
          </GlassCard>
        )}

        {/* ── Exam Form ─────────────────────────────────────────────────── */}
        <ExamForm
          exam={exam as unknown as Exam} // Type assertion to satisfy ExamForm's expected type
          onChange={(updates) => setExam((prev) => ({ ...prev, ...updates }))}
        />

        <hr className="divider" />

        {/* ── Question List ─────────────────────────────────────────────── */}
        <QuestionList
          questions={exam.questions ?? []}
          onChange={(questions) => setExam((prev) => ({ ...prev, questions }))}
        />

        {/* ── Sticky Mobile Footer ──────────────────────────────────────── */}
        <div className="sm:hidden fixed bottom-0 left-0 right-0 p-4 bg-[var(--background)] border-t border-[var(--border-subtle)] z-50">
          <Button
            variant="primary"
            className="w-full shadow-glow"
            onClick={handleUpdate}
            disabled={loading}
          >
            {loading ? "Saving..." : "Apply Final Changes"}
          </Button>
        </div>

      </div>
    </div>
  );
}