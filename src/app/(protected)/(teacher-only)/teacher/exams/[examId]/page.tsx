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
import { toast } from "sonner";
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
              <Link href={`/teacher/exams/${examId}/results`}>
                <Button variant="outline" size="sm">
                  <Target className="mr-2 h-4 w-4" /> View Results
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

            {/* Sections & Questions */}
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">Exam Sections & Questions ({(exam.questions ?? []).length} Questions)</h3>
              </div>

              {(() => {
                // Group questions by section
                const sectionMap = new Map<string, NonNullable<typeof exam.questions>>();
                (exam.questions ?? []).forEach((q) => {
                  const secName = q.section?.trim() || "Section A";
                  if (!sectionMap.has(secName)) sectionMap.set(secName, []);
                  sectionMap.get(secName)!.push(q);
                });

                const sortedSections = Array.from(sectionMap.entries()).sort(([a], [b]) => a.localeCompare(b));

                if (sortedSections.length === 0) {
                  return (
                    <GlassCard padding="md" className="text-center p-8 text-[var(--text-muted)]">
                      No questions in this exam.
                    </GlassCard>
                  );
                }

                return sortedSections.map(([secName, secQuestions = []]) => {
                  const firstQ = secQuestions[0];
                  const secType = firstQ?.questionType || "MULTIPLE_CHOICE";
                  const secMarksPerQ = firstQ?.marks || 1;
                  const totalSecMarks = secQuestions.reduce((sum, q) => sum + (q.marks || 0), 0);

                  return (
                    <div key={secName} className="space-y-3">
                      <div className="flex items-center justify-between bg-[var(--surface-2)] px-4 py-2.5 rounded-xl border border-[var(--border-subtle)]">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white text-base">{secName}</span>
                          <Badge variant="neutral" className="text-[10px]">
                            {secType.replace(/_/g, " ")}
                          </Badge>
                          <Badge variant="default" className="text-[10px]">
                            {secMarksPerQ} Marks / Q
                          </Badge>
                        </div>
                        <span className="text-xs text-[var(--text-muted)]">
                          {secQuestions.length} {secQuestions.length === 1 ? "Question" : "Questions"} ({totalSecMarks} Marks)
                        </span>
                      </div>

                      <div className="space-y-3 pl-2 border-l-2 border-indigo-500/20">
                        {secQuestions.map((q, idx) => (
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
                  );
                })
              })()}
            </div>
          </div>

          {/* Sidebar / Quick Stats */}
          <div className="space-y-6">
            <GlassCard padding="lg" className="bg-indigo-500/5 border-indigo-500/20 space-y-6">
              <div>
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
                    <span className="text-[var(--text-muted)]">Access Mode</span>
                    <Badge variant={exam.isPublic !== false ? "success" : "warning"} className="text-[10px]">
                      {exam.isPublic !== false ? "Public" : "Code Required"}
                    </Badge>
                  </div>
                  {exam.isPublic === false && (
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-[var(--text-muted)]">Exam Code</span>
                      <span className="font-mono text-xs bg-zinc-800 px-2 py-0.5 rounded text-amber-300 font-bold">
                        {exam.examCode || "N/A"}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-[var(--text-muted)]">Negative Marking</span>
                    <span className="text-white font-medium text-xs">
                      {exam.negativeMarking ? `-${exam.negativeMarks} Marks` : "Disabled"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-[var(--text-muted)]">Results Status</span>
                    <Badge variant={exam.isResultsReleased ? "success" : "neutral"} className="text-[10px]">
                      {exam.isResultsReleased ? "Released" : "Pending Release"}
                    </Badge>
                  </div>
                </div>
              </div>

              <hr className="border-[var(--border-subtle)]" />

              {/* Release Results Action */}
              <div className="space-y-2">
                <Button
                  type="button"
                  variant={exam.isResultsReleased ? "outline" : "primary"}
                  className="w-full shadow-glow"
                  disabled={exam.isResultsReleased}
                  onClick={async () => {
                    try {
                      const res = await api.post(`/api/v1/exams/${examId}/release-results`);
                      setExam(res.data);
                      toast.success("Exam results and answer keys released to students!");
                    } catch {
                      toast.error("Failed to release exam results.");
                    }
                  }}
                >
                  {exam.isResultsReleased ? "Results Released" : "Evaluate & Release Results"}
                </Button>
                <p className="text-[11px] text-[var(--text-muted)] text-center">
                  {exam.isResultsReleased
                    ? "Students can now view their scores and the full answer key."
                    : "Clicking this allows all students to view their scores and answer key at the same time."}
                </p>
              </div>

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
