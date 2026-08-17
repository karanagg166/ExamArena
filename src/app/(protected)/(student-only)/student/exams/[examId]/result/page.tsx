"use client";

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { GlassCard } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAttemptStore } from '@/stores/useAttemptStore';
import { api } from '@/lib/axios';
import { CheckCircle2, Clock, ArrowRight, Award, Check, HelpCircle } from 'lucide-react';
import type { Exam, StudentExam } from '@/types';

export default function ExamResultPage() {
    const { examId } = useParams<{ examId: string }>();
    const router = useRouter();
    const [exam, setExam] = useState<Exam | null>(null);
    const [attempt, setAttempt] = useState<StudentExam | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Ensure active timer is cleared
        useAttemptStore.getState().clearAttempt();

        const loadExamAndAttempt = async () => {
            if (!examId) return;
            try {
                const [examRes, studentExamsRes] = await Promise.all([
                    api.get(`/api/v1/exams/${examId}`).catch(() => null),
                    api.get('/api/v1/exams/student').catch(() => null),
                ]);

                if (examRes?.data) {
                    setExam(examRes.data);
                }

                if (studentExamsRes?.data && Array.isArray(studentExamsRes.data)) {
                    const match = studentExamsRes.data.find((e: { id: string; attemptId?: string }) => e.id === examId);
                    if (match?.attemptId) {
                        const attRes = await api.get(`/api/v1/attempts/${match.attemptId}`).catch(() => null);
                        if (attRes?.data) {
                            setAttempt(attRes.data);
                        }
                    }
                }
            } catch (e) {
                console.error("Error loading result details:", e);
            } finally {
                setLoading(false);
            }
        };

        void loadExamAndAttempt();
    }, [examId]);

    const isReleased = exam?.isResultsReleased ?? attempt?.isResultsReleased ?? false;

    if (loading) {
        return (
            <div className="page-shell flex items-center justify-center min-h-[60vh]">
                <div className="w-10 h-10 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="page-shell flex items-center justify-center min-h-[80vh] py-8">
            <div className="max-w-2xl w-full mx-4 space-y-6 animate-fade-in">
                {/* Status Hero Card */}
                <GlassCard className="p-8 sm:p-12 text-center space-y-6">
                    <div className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto ring-4 ${
                        isReleased ? "bg-indigo-500/10 ring-indigo-500/20 text-indigo-400" : "bg-green-500/10 ring-green-500/20 text-green-400"
                    }`}>
                        {isReleased ? <Award className="w-10 h-10" /> : <CheckCircle2 className="w-10 h-10" />}
                    </div>

                    <div className="space-y-2">
                        <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                            {isReleased ? "Exam Results Released" : "Exam Submitted Successfully"}
                        </h2>
                        <p className="text-[var(--text-muted)] text-sm sm:text-base leading-relaxed max-w-lg mx-auto">
                            {isReleased
                                ? "Your teacher has evaluated and released the results for this exam. See your total score and answer breakdown below."
                                : "Your submission has been securely recorded. The teacher will evaluate and release results soon. Your score and answer key will become available automatically once released."}
                        </p>
                    </div>

                    {isReleased && attempt && exam && (
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 text-left">
                            <div>
                                <p className="text-xs text-zinc-400">Score Obtained</p>
                                <p className="text-xl font-bold text-emerald-400 mt-0.5">
                                    {attempt.marksObtained} <span className="text-xs text-zinc-500 font-normal">/ {exam.maxMarks}</span>
                                </p>
                            </div>
                            <div>
                                <p className="text-xs text-zinc-400">Percentage</p>
                                <p className="text-xl font-bold text-white mt-0.5">
                                    {exam.maxMarks > 0 ? `${((attempt.marksObtained / exam.maxMarks) * 100).toFixed(1)}%` : "N/A"}
                                </p>
                            </div>
                            <div className="col-span-2 sm:col-span-1">
                                <p className="text-xs text-zinc-400">Status</p>
                                <Badge variant="success" className="mt-1 text-xs">
                                    Graded
                                </Badge>
                            </div>
                        </div>
                    )}

                    {!isReleased && (
                        <div className="p-4 rounded-xl border border-amber-500/20 bg-amber-500/10 text-amber-300 text-xs flex items-center justify-center gap-2">
                            <Clock className="w-4 h-4 shrink-0" />
                            <span>Results and full answer keys are currently pending teacher release.</span>
                        </div>
                    )}

                    <div className="pt-4 border-t border-[var(--border-subtle)] flex flex-col sm:flex-row items-center justify-center gap-3">
                        <Button 
                            onClick={() => router.push('/student/exams')} 
                            variant="primary" 
                            size="lg"
                            className="w-full sm:w-auto min-w-[200px]"
                        >
                            Back to Exams <ArrowRight className="w-5 h-5 ml-2" />
                        </Button>
                    </div>
                </GlassCard>

                {/* Answer Key Breakdown if Released */}
                {isReleased && exam?.questions && exam.questions.length > 0 && (
                    <div className="space-y-4">
                        <h3 className="text-lg font-bold text-white flex items-center gap-2">
                            <HelpCircle className="w-5 h-5 text-indigo-400" /> Answer Key & Explanations
                        </h3>

                        {exam.questions.map((q, idx) => {
                            const studentAns = (attempt?.answers || []).find((a) => a.questionId === q.id);
                            const selectedOptIds = new Set(studentAns?.selectedOptions?.map((o) => o.optionId) || []);
                            const isAttempted = Boolean(
                              (studentAns?.selectedOptions && studentAns.selectedOptions.length > 0) ||
                              (studentAns?.textAnswer && studentAns.textAnswer.trim() !== "")
                            );
                            const correctness = studentAns?.isCorrect;
                            const marksAwarded = studentAns?.marksAwarded ?? 0;

                            return (
                                <GlassCard key={q.id} padding="md" className="space-y-3">
                                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-zinc-800/80 pb-2.5">
                                        <div className="flex items-center gap-2 flex-wrap">
                                            <p className="text-sm font-semibold text-white">
                                                Q{idx + 1}. {q.text}
                                            </p>
                                            {q.questionType === "MULTIPLE_SELECT" && (
                                              <span className="text-[10px] text-amber-300 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded font-medium">
                                                Multi-Select (Partial Marking)
                                              </span>
                                            )}
                                        </div>
                                        <div className="flex items-center gap-2 shrink-0">
                                            {correctness === "FULLY_CORRECT" && (
                                              <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                                                <Check className="w-3 h-3" /> Fully Correct (+{marksAwarded} Marks)
                                              </span>
                                            )}
                                            {correctness === "PARTIALLY_CORRECT" && (
                                              <span className="px-2 py-0.5 text-xs font-semibold rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1">
                                                <Award className="w-3 h-3" /> Partially Correct (+{marksAwarded} / {q.marks} Marks)
                                              </span>
                                            )}
                                            {correctness === "INCORRECT" && isAttempted && (
                                              <span className="px-2 py-0.5 text-xs font-semibold rounded bg-red-500/10 text-red-400 border border-red-500/20">
                                                Incorrect ({marksAwarded < 0 ? `${marksAwarded}` : "0"} / {q.marks} Marks)
                                              </span>
                                            )}
                                            {!isAttempted && (
                                              <span className="px-2 py-0.5 text-xs font-semibold rounded bg-zinc-800 text-zinc-400">
                                                Unattempted (0 / {q.marks} Marks)
                                              </span>
                                            )}
                                        </div>
                                    </div>

                                    {/* Options */}
                                    {q.options && q.options.length > 0 && (
                                        <div className="space-y-1.5 pt-1">
                                            {q.options.map((opt) => {
                                                const isSelected = selectedOptIds.has(opt.id);
                                                const isCorrect = opt.isCorrect;

                                                let itemStyle = "border-zinc-800 bg-zinc-900/40 text-zinc-300";
                                                if (isSelected && isCorrect) {
                                                    itemStyle = "border-emerald-500/50 bg-emerald-500/15 text-emerald-300 font-medium ring-1 ring-emerald-500/20";
                                                } else if (isSelected && !isCorrect) {
                                                    itemStyle = "border-red-500/50 bg-red-500/15 text-red-300 ring-1 ring-red-500/20";
                                                } else if (!isSelected && isCorrect) {
                                                    itemStyle = "border-emerald-500/30 bg-emerald-950/20 text-emerald-400/90 border-dashed";
                                                }

                                                return (
                                                    <div
                                                        key={opt.id}
                                                        className={`p-2.5 rounded-lg border text-xs flex items-center justify-between ${itemStyle}`}
                                                    >
                                                        <div className="flex items-center gap-2">
                                                            <span className="font-bold opacity-75">{opt.optionNumber}.</span>
                                                            <span>{opt.text}</span>
                                                        </div>
                                                        <div className="flex items-center gap-1 text-[11px]">
                                                            {isSelected && !isCorrect && (
                                                                <span className="px-1.5 py-0.5 rounded bg-red-500/20 text-red-300 text-[10px] font-medium border border-red-500/30">
                                                                    Your Choice (Incorrect)
                                                                </span>
                                                            )}
                                                            {isSelected && isCorrect && (
                                                                <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-medium border border-emerald-500/30 flex items-center gap-0.5">
                                                                    <Check className="w-3 h-3" /> Your Choice (Correct)
                                                                </span>
                                                            )}
                                                            {!isSelected && isCorrect && (
                                                                <span className="px-1.5 py-0.5 rounded bg-zinc-800 text-emerald-400 text-[10px] font-medium border border-emerald-500/20 flex items-center gap-0.5">
                                                                    <Check className="w-3 h-3" /> Correct Option (Missed)
                                                                </span>
                                                            )}
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    )}

                                    {q.explanation && (
                                        <div className="p-2.5 rounded-lg bg-zinc-900/80 border border-zinc-800/80 text-xs text-zinc-400">
                                            <span className="text-zinc-300 font-semibold">Explanation: </span>
                                            {q.explanation}
                                        </div>
                                    )}
                                </GlassCard>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
