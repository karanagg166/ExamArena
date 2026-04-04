"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/axios";
import { PageHeader } from "@/components/ui/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Calendar,
  Clock,
  FileText,
  User,
  School,
  ArrowLeft,
  HelpCircle,
} from "lucide-react";
import { format } from "date-fns";
import type { Exam } from "@/types";
import { useAuthStore } from "@/stores/useAuthStore";

export default function ExamDetailViewPage() {
  const { examId } = useParams();
  const router = useRouter();
  const [exam, setExam] = useState<Exam | null>(null);
  const [loading, setLoading] = useState(true);
  const user = useAuthStore((state) => state.user);

  // We no longer automatically redirect, to avoid flash/confusion.
  // Instead, we immediately intercept the rendering below.

  useEffect(() => {
    async function fetchExam() {
      try {
        const response = await api.get(`/api/v1/exams/${examId}`);
        setExam(response.data);
      } catch (error) {
        console.error("Error fetching exam:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchExam();
  }, [examId]);

  if (loading)
    return (
      <div className="p-8 text-center text-[var(--text-dimmed)]">
        Loading assessment profile...
      </div>
    );
  if (!exam)
    return (
      <div className="p-8 text-center text-[var(--text-dimmed)]">
        Assessment not found.
      </div>
    );

  return (
    <div className="container mx-auto py-8 px-4 max-w-5xl">
      <Button
        variant="outline"
        onClick={() => router.back()}
        className="mb-6 hover:bg-white/10"
      >
        <ArrowLeft className="w-4 h-4 mr-2" /> Back to Discovery
      </Button>

      <PageHeader
        title={exam.name}
        description={exam.description}
        className="mb-8"
        actions={
          <div className="flex flex-wrap gap-3">
            <Badge variant="default" className="px-3 py-1 text-sm">
              {exam.type}
            </Badge>
            {exam.subject && (
              <Badge
                variant="neutral"
                className="px-3 py-1 text-sm border-white/10 uppercase"
              >
                {exam.subject.replace("_", " ")}
              </Badge>
            )}
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Metadata & Questions */}
        <div className="lg:col-span-2 space-y-8">
          <GlassCard padding="lg">
            <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
              <FileText className="w-5 h-5 text-[var(--accent)]" />
              General Instructions
            </h2>
            <div className="text-[var(--text-secondary)] bg-white/5 p-6 rounded-2xl border border-white/5 whitespace-pre-wrap leading-relaxed">
              {exam.instructions ||
                "No specific instructions provided for this assessment."}
            </div>
          </GlassCard>

          {/* Question Preview Structure */}
          <section className="space-y-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-2">
              <HelpCircle className="w-6 h-6 text-violet-400" />
              Assessment Structure
            </h2>
            <p className="text-[var(--text-dimmed)] text-sm mb-6">
              Preview the format and scoring for each question included in this
              exam.
            </p>

            <div className="space-y-4">
              {exam.questions
                ?.sort((a, b) => a.questionNumber - b.questionNumber)
                .map((q, idx) => (
                  <GlassCard
                    key={idx}
                    padding="md"
                    className="border-white/5 hover:border-[var(--accent)]/30 transition-colors"
                  >
                    <div className="flex justify-between items-start gap-4">
                      <div className="flex items-start gap-3 w-full">
                        <div className="w-8 h-8 rounded-lg bg-[var(--accent)]/10 flex items-center justify-center shrink-0 border border-[var(--accent)]/20 mt-1">
                          <span className="text-[var(--accent)] font-bold text-sm">
                            {q.questionNumber}
                          </span>
                        </div>
                        <div className="space-y-3 w-full">
                          <div className="space-y-1">
                            <p className="text-[var(--text-primary)] font-medium leading-relaxed">
                              {q.text}
                            </p>
                            <div className="flex flex-wrap gap-2 pt-1">
                              <Badge
                                variant="neutral"
                                className="text-[10px] uppercase tracking-tighter opacity-70"
                              >
                                {q.questionType.replace("_", " ")}
                              </Badge>
                              {q.wordLimit && (
                                <Badge
                                  variant="neutral"
                                  className="text-[10px] uppercase tracking-tighter opacity-70"
                                >
                                  {q.wordLimit} Word Limit
                                </Badge>
                              )}
                            </div>
                          </div>

                          {user?.role !== "STUDENT" &&
                            q.options &&
                            q.options.length > 0 && (
                              <div className="space-y-2 mt-4 pl-3 border-l-2 border-[var(--border-subtle)]">
                                {q.options
                                  .sort(
                                    (a, b) => a.optionNumber - b.optionNumber,
                                  )
                                  .map((opt) => (
                                    <div
                                      key={opt.id}
                                      className={`px-3 py-2.5 rounded-lg text-sm border flex items-center justify-between ${opt.isCorrect ? "bg-green-500/10 border-green-500/30 text-green-300" : "bg-[var(--surface-1)] border-[var(--border-subtle)] text-[var(--text-muted)]"}`}
                                    >
                                      <span>{opt.text}</span>
                                      {opt.isCorrect && (
                                        <span className="ml-2 text-[10px] font-bold uppercase tracking-wider text-green-400 opacity-80 shrink-0">
                                          Correct
                                        </span>
                                      )}
                                    </div>
                                  ))}
                              </div>
                            )}

                          {user?.role !== "STUDENT" && q.explanation && (
                            <div className="text-xs text-[var(--text-dimmed)] bg-white/5 p-3 rounded-lg border border-white/5 mt-3 leading-relaxed">
                              <span className="font-semibold text-white/70 block mb-1">
                                Explanation / Rubric
                              </span>
                              {q.explanation}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="px-3 py-1 bg-white/5 rounded-full border border-white/10 text-xs font-semibold text-[var(--text-secondary)] shrink-0 mt-1">
                        {q.marks} Marks
                      </div>
                    </div>
                  </GlassCard>
                ))}

              {(!exam.questions || exam.questions.length === 0) && (
                <div className="text-center p-12 bg-white/5 rounded-3xl border border-dashed border-white/10 text-[var(--text-dimmed)]">
                  Structural details are not yet available for this assessment.
                </div>
              )}
            </div>
          </section>
        </div>

        {/* Right Column: Information Sidebar */}
        <div className="space-y-6">
          <GlassCard
            padding="lg"
            className="border-[var(--accent)]/20 bg-[var(--accent)]/5"
          >
            <h3 className="font-bold text-white mb-6 uppercase text-xs tracking-widest opacity-80">
              Examination Profile
            </h3>

            <div className="space-y-5">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-[var(--accent)]/10 flex items-center justify-center text-[var(--accent)] border border-[var(--accent)]/20">
                  <Calendar className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-xs text-[var(--text-dimmed)] font-medium">
                    Scheduled At
                  </p>
                  <p className="text-sm font-semibold text-white">
                    {format(new Date(exam.scheduledAt), "PPP p")}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-violet-500/10 flex items-center justify-center text-violet-400 border border-violet-500/20">
                  <Clock className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-xs text-[var(--text-dimmed)] font-medium">
                    Duration
                  </p>
                  <p className="text-sm font-semibold text-white">
                    {exam.duration} Minutes
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 border border-emerald-500/20">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-xs text-[var(--text-dimmed)] font-medium">
                    Total Volume
                  </p>
                  <p className="text-sm font-semibold text-white">
                    {exam.maxMarks} Marks / {exam.questions?.length ?? 0} Items
                  </p>
                </div>
              </div>
            </div>
          </GlassCard>

          {/* Teacher Profile Card */}
          <GlassCard padding="lg">
            <h3 className="font-bold text-white mb-6 uppercase text-xs tracking-widest opacity-80">
              Conducted By
            </h3>

            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-[var(--surface-3)] border border-white/10 flex items-center justify-center text-violet-400">
                  <User className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm font-bold text-white">
                    {exam.teacher?.user.name}
                  </p>
                  <p className="text-xs text-[var(--text-dimmed)]">
                    Lead Instructor
                  </p>
                </div>
              </div>

              {exam.teacher?.school && (
                <div className="flex items-center gap-3 pt-4 border-t border-white/5">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/5 border border-emerald-500/10 flex items-center justify-center text-emerald-400">
                    <School className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-[var(--text-secondary)]">
                      {exam.teacher.school.name}
                    </p>
                    <p className="text-[10px] text-[var(--text-dimmed)] uppercase tracking-wider">
                      Host Institution
                    </p>
                  </div>
                </div>
              )}
            </div>
          </GlassCard>

          {user?.role === "STUDENT" ||
          user?.role?.toLowerCase() === "student" ? (
            <Button
              onClick={() => router.push(`/student/exams/${exam.id}/start`)}
              className="w-full py-6 rounded-2xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:scale-[1.02] transition-transform shadow-xl shadow-sky-500/20 text-white font-semibold"
            >
              Give the Assessment
            </Button>
          ) : (
            <>
              <Button className="w-full py-6 rounded-2xl bg-gradient-to-r from-[var(--accent)] to-violet-600 hover:scale-[1.02] transition-transform shadow-xl shadow-[var(--accent)]/20 group">
                View Assessment Stats
              </Button>
              <p className="text-center text-[10px] text-[var(--text-muted)] italic">
                * Action available for administrators and instructors.
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
