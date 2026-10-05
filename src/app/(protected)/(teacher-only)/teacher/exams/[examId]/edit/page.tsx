"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, Save, FileUp } from "lucide-react";
import Link from "next/link";

import { PageHeader } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";
import { FormMessage } from "@/components/ui/form-message";
import { GlassCard } from "@/components/ui/glass-card";
import { ExamForm } from "@/components/exam/ExamForm";
import { QuestionList } from "@/components/question/QuestionList";
import { QuestionImportModal } from "@/components/imports";
import { api } from "@/lib/axios";
import { getErrorMessage } from "@/lib/error";
import { validateExam, computeMaxMarks } from "@/lib/exam-validation";
import type { ExamUpdate, Exam } from "@/types";

export default function EditExamPage() {
  const { examId } = useParams();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);

  const [exam, setExam] = useState<ExamUpdate>({
    id: examId as string,
    name: "",
    examCode: "",
    accessPassword: "",
    hasAccessPassword: false,
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

  // ── Fetch Initial Data ───────────────────────────────────────────────────
  const fetchExam = useCallback(async () => {
    try {
      const response = await api.get(`/api/v1/exams/${examId}`);
      const data = response.data as Exam;

      setExam({
        id: data.id,
        name: data.name,
        examCode: data.examCode || "",
        accessPassword: "",
        hasAccessPassword: data.hasAccessPassword || Boolean(data.accessPassword),
        description: data.description,
        scheduledAt: data.scheduledAt,
        duration: data.duration,
        type: data.type,
        maxMarks: data.maxMarks,
        isPublished: data.isPublished,
        isPublic: data.isPublic !== false,
        negativeMarking: Boolean(data.negativeMarking),
        negativeMarks: data.negativeMarks || 0,
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
  }, [examId]);

  useEffect(() => {
    if (examId) fetchExam();
  }, [examId, fetchExam]);

  // ── Auto-compute maxMarks from questions ─────────────────────────────────
  const computedMaxMarks = useMemo(
    () => computeMaxMarks(exam.questions ?? []),
    [exam.questions]
  );

  // ── Submit ────────────────────────────────────────────────────────────────
  const handleUpdate = async () => {
    setErrorText(null);

    const validationError = validateExam(exam);
    if (validationError) return setErrorText(validationError);

    setLoading(true);
    try {
      const payload: Record<string, unknown> = {
        ...exam,
        maxMarks: computedMaxMarks,
      };

      const trimmedPassword = exam.accessPassword?.trim();
      if (!trimmedPassword) {
        delete payload.accessPassword;
      } else {
        payload.accessPassword = trimmedPassword;
      }

      await api.patch(`/api/v1/exams/${examId}`, payload);
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
            <div className="flex gap-2 sm:gap-3">
              <Button
                variant="outline"
                type="button"
                onClick={() => setIsImportModalOpen(true)}
                className="border-indigo-500/40 text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10"
              >
                <FileUp className="mr-2 h-4 w-4" /> Import Paper
              </Button>
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
          exam={{ ...exam, maxMarks: computedMaxMarks } as unknown as Exam}
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

        {/* ── Question Import Modal ────────────────────────────────────── */}
        <QuestionImportModal
          isOpen={isImportModalOpen}
          onClose={() => setIsImportModalOpen(false)}
          examId={examId as string}
          onSuccess={fetchExam}
        />

      </div>
    </div>
  );
}