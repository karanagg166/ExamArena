"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Edit3,
  Calendar,
  Clock,
  FileText,
  AlertCircle,
  ChevronRight,
  Target
} from "lucide-react";
import Link from "next/link";

import { PageHeader } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/axios";
import type { Exam } from "@/types";
import { format } from "date-fns";

export default function ExamViewPage() {
  const { examId } = useParams();
  const router = useRouter();
  const [exam, setExam] = useState<Exam | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchExam = async () => {
      try {
        const response = await api.get(`/api/v1/exams/${examId}`);
        setExam(response.data);
      } catch (err: unknown) {
        setError((err as { response?: { data?: { detail?: string } } }).response?.data?.detail || "Failed to load exam details.");
      } finally {
        setLoading(false);
      }
    };

    if (examId) fetchExam();
  }, [examId]);

  if (loading) {
    return (
      <div className="page-shell flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
          <p className="text-[var(--text-muted)] animate-pulse">Loading exam details...</p>
        </div>
      </div>
    );
  }

  if (error || !exam) {
    return (
      <div className="page-shell">
        <GlassCard className="max-w-2xl mx-auto p-12 text-center space-y-6">
          <div className="mx-auto w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-white">Oops! Something went wrong</h2>
            <p className="text-[var(--text-muted)]">{error || "Exam not found"}</p>
          </div>
          <Button onClick={() => router.push("/teacher/exams")} variant="secondary">
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to Exams
          </Button>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="page-shell">
      <div className="max-w-5xl mx-auto space-y-8 animate-fade-in">

        <PageHeader
          overline="Exam Overview"
          title={exam.name}
          subtitle={exam.description}
          actions={
            <div className="flex gap-3">
              <Link href="/teacher/exams">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="mr-2 h-4 w-4" /> Back
                </Button>
              </Link>
              <Link href={`/teacher/exams/${examId}/edit`}>
                <Button variant="primary" size="sm" className="shadow-glow">
                  <Edit3 className="mr-2 h-4 w-4" /> Edit Exam
                </Button>
              </Link>
            </div>
          }
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Details */}
          <div className="lg:col-span-2 space-y-6">
            <GlassCard padding="lg" className="space-y-6">
              <div className="flex items-center gap-2 text-indigo-400 font-medium">
                <FileText className="w-5 h-5" />
                <h3>About this Exam</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-[var(--surface-3)] text-zinc-400">
                    <Calendar className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-xs text-[var(--text-dimmed)] uppercase tracking-wider font-bold">Scheduled Date</p>
                    <p className="text-[var(--text-primary)] font-medium">
                      {format(new Date(exam.scheduledAt), "PPP p")}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-[var(--surface-3)] text-zinc-400">
                    <Clock className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-xs text-[var(--text-dimmed)] uppercase tracking-wider font-bold">Duration</p>
                    <p className="text-[var(--text-primary)] font-medium">{exam.duration} Minutes</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-[var(--surface-3)] text-zinc-400">
                    <Target className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-xs text-[var(--text-dimmed)] uppercase tracking-wider font-bold">Total Marks</p>
                    <p className="text-[var(--text-primary)] font-medium">{exam.maxMarks} Marks</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-[var(--surface-3)] text-zinc-400">
                    <Badge variant={exam.isPublished ? "success" : "neutral"} className="mt-0.5">
                      {exam.isPublished ? "Published" : "Draft"}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-xs text-[var(--text-dimmed)] uppercase tracking-wider font-bold">Status</p>
                    <p className="text-[var(--text-primary)] font-medium">
                      {exam.isPublished ? "Visible to Students" : "Only You Can See This"}
                    </p>
                  </div>
                </div>
              </div>

              {exam.instructions && (
                <div className="pt-6 border-t border-[var(--border-subtle)] space-y-3">
                  <h4 className="text-sm font-semibold text-white">Student Instructions</h4>
                  <div className="p-4 rounded-xl bg-[var(--surface-1)] text-[var(--text-muted)] text-sm leading-relaxed whitespace-pre-wrap">
                    {exam.instructions}
                  </div>
                </div>
              )}
            </GlassCard>

            {/* Questions Summary */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">Questions ({(exam.questions ?? []).length})</h3>
              </div>

              <div className="space-y-3">
                {(exam.questions ?? []).map((q, idx) => (
                  <GlassCard key={q.id} padding="md" className="space-y-4 hover:bg-[var(--surface-2)] transition-colors">
                    <div className="flex items-start gap-4">
                      <div className="w-8 h-8 rounded-full bg-[var(--surface-3)] flex items-center justify-center text-xs font-bold text-indigo-400 shrink-0">
                        {idx + 1}
                      </div>
                      <div className="flex-grow space-y-2 pe-4">
                        <p className="text-[var(--text-primary)] font-medium whitespace-pre-wrap">{q.text}</p>
                        <div className="flex flex-wrap gap-2">
                          <Badge variant="neutral" className="text-[10px] lowercase">
                            {q.questionType.replace("_", " ")}
                          </Badge>
                          <Badge variant="default" className="text-[10px]">
                            {q.marks} Marks
                          </Badge>
                          {q.section && (
                            <span className="text-[10px] text-[var(--text-dimmed)] italic">Section: {q.section}</span>
                          )}
                          {q.wordLimit && (
                            <span className="text-[10px] text-[var(--text-dimmed)] italic">Word Limit: {q.wordLimit}</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {(q.options ?? []).length > 0 && (
                      <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-1)] p-4 space-y-2">
                        <p className="text-xs font-semibold tracking-wider uppercase text-[var(--text-dimmed)]">Options</p>
                        <div className="space-y-2">
                          {(q.options ?? []).map((opt) => (
                            <div
                              key={opt.id}
                              className={`flex items-start justify-between gap-3 rounded-lg px-3 py-2 border ${opt.isCorrect
                                ? "border-emerald-500/40 bg-emerald-500/10"
                                : "border-[var(--border-subtle)] bg-[var(--surface-2)]"
                                }`}
                            >
                              <p className="text-sm text-[var(--text-primary)]">{opt.optionNumber}. {opt.text || "--"}</p>
                              {opt.isCorrect && (
                                <Badge variant="success" className="text-[10px] shrink-0">Correct</Badge>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {q.explanation && (
                      <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-1)] p-4 space-y-1">
                        <p className="text-xs font-semibold tracking-wider uppercase text-[var(--text-dimmed)]">Explanation</p>
                        <p className="text-sm text-[var(--text-muted)] whitespace-pre-wrap">{q.explanation}</p>
                      </div>
                    )}
                  </GlassCard>
                ))}
              </div>
            </div>
          </div>

          {/* Sidebar / Quick Stats */}
          <div className="space-y-6">
            <GlassCard padding="lg" className="bg-indigo-500/5 border-indigo-500/20">
              <h4 className="text-sm font-semibold text-white mb-4">Exam Summary</h4>
              <div className="space-y-4">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-[var(--text-muted)]">Total Questions</span>
                  <span className="text-white font-medium">{(exam.questions ?? []).length}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-[var(--text-muted)]">Max Marks</span>
                  <span className="text-white font-medium">{exam.maxMarks}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-[var(--text-muted)]">Avg Marks/Q</span>
                  <span className="text-white font-medium">
                    {((exam.questions ?? []).length > 0 ? (exam.maxMarks / (exam.questions ?? []).length).toFixed(1) : 0)}
                  </span>
                </div>
              </div>
              <hr className="my-4 border-[var(--border-subtle)]" />
              <Link href={`/teacher/exams/${examId}/edit`}>
                <Button className="w-full" variant="outline">
                  Manage Questions
                  <ChevronRight className="ml-1 h-4 w-4" />
                </Button>
              </Link>
            </GlassCard>
          </div>
        </div>
      </div>
    </div>
  );
}
