"use client";

import React, { useEffect, useState, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAttemptEngine } from '@/hooks/useAttemptEngine';
import { api } from '@/lib/axios';
import { AttemptQuestion } from '@/components/attempt/AttemptQuestion';
import { AttemptSummary } from '@/components/attempt/AttemptSummary';
import { ExamTimer } from '@/components/attempt/ExamTimer';
import { Button } from '@/components/ui/button';
import { ChevronRight, ChevronLeft, Send, AlertCircle, Maximize, PanelRightOpen, PanelRightClose, X } from 'lucide-react';
import { GlassCard } from '@/components/ui/glass-card';
import { useProctoring } from '@/hooks/useProctoring';
import { ProctoringWarning } from '@/components/attempt/ProctoringWarning';

export default function ExamAttemptPage() {
    const { examId } = useParams();
    const router = useRouter();
    const { 
        examId: currentExamId, 
        attemptId, 
        status, 
        activeQuestionId, 
        setActiveQuestion,
        answers,
        submitAttemptLocal,
        clearAttempt
    } = useAttemptEngine();

    const [exam, setExam] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [showConfirmSubmit, setShowConfirmSubmit] = useState(false);

    const [warningVisible, setWarningVisible] = useState(false);
    const [warningReason, setWarningReason] = useState("");
    const [warningDisplayCount, setWarningDisplayCount] = useState(0);

    const handleWarning = useCallback((count: number, reason: string) => {
        setWarningReason(reason);
        setWarningDisplayCount(count);
        setWarningVisible(true);
    }, []);

    useEffect(() => {
        if (!attemptId || status !== 'IN_PROGRESS' || currentExamId !== examId) {
             router.replace(`/student/exams/${examId}/start`);
             return;
        }

        const fetchExamAndEnsureSync = async () => {
            try {
                const res = await api.get(`/api/v1/exams/${examId}`);
                setExam(res.data);
            } catch (err) {
                setError("Failed to load exam data. Check your connection.");
            } finally {
                setLoading(false);
            }
        };

        fetchExamAndEnsureSync();
    }, [examId, attemptId, status, currentExamId, router]);

    const handleSubmit = useCallback(async () => {
        if (!attemptId) return;
        setSubmitting(true);
        setShowConfirmSubmit(false);
        try {
            const formattedAnswers = Object.values(answers).map(ans => ({
                id: ans.id,
                textAnswer: ans.textAnswer,
                selectedOptions: ans.selectedOptions
            }));

            await api.post('/api/v1/attempts/submit', {
                id: attemptId,
                answers: formattedAnswers
            });

            submitAttemptLocal();
            clearAttempt();

            if (document.fullscreenElement) {
                document.exitFullscreen().catch(()=>{});
            }

            router.replace(`/student/exams/${examId}/result`);
        } catch (err: any) {
            console.error("Submission failed", err);
            const msg = err.response?.data?.detail || "Failed to submit exam. Please check your connection and try again.";
            alert(msg);
            setSubmitting(false);
        }
    }, [answers, attemptId, examId, submitAttemptLocal, clearAttempt, router]);

    const proctoring = useProctoring({
        maxWarnings: 3,
        onWarning: handleWarning,
        onAutoSubmit: handleSubmit,
        onFullscreenExit: () => {},
        enabled: !!(exam && status === 'IN_PROGRESS' && !submitting)
    });


    if (loading) {
        return (
            <div className="min-h-screen bg-[var(--background)] flex items-center justify-center">
                <div className="w-10 h-10 border-4 border-[var(--accent)]/30 border-t-[var(--accent)] rounded-full animate-spin" />
            </div>
        );
    }

    if (error || !exam) {
        return (
             <div className="min-h-screen bg-[var(--background)] flex items-center justify-center p-6">
                <GlassCard className="max-w-md w-full p-8 text-center space-y-6">
                    <AlertCircle className="w-12 h-12 text-red-500 mx-auto" />
                    <p className="text-[var(--text-primary)] text-lg">{error}</p>
                    <Button onClick={() => window.location.reload()} variant="primary">Retry</Button>
                </GlassCard>
            </div>
        )
    }

    const unansweredCount = Object.values(answers).filter(a => a.status === 'NOT_VISITED' || a.status === 'VISITED_NOT_ANSWERED').length;
    const hasUnanswered = unansweredCount > 0;

    const questions = exam.questions || [];
    const currentIndex = questions.findIndex((q: any) => q.id === activeQuestionId);
    const activeQuestion = currentIndex !== -1 ? questions[currentIndex] : questions[0];

    const goToNext = () => {
        if (currentIndex < questions.length - 1) {
            setActiveQuestion(questions[currentIndex + 1].id);
        }
    };

    const goToPrev = () => {
        if (currentIndex > 0) {
            setActiveQuestion(questions[currentIndex - 1].id);
        }
    };

    useEffect(() => {
        if (!activeQuestionId && questions && questions.length > 0) {
           setActiveQuestion(questions[0].id);
        }
    }, [activeQuestionId, questions, setActiveQuestion]);

    if (!activeQuestionId && questions && questions.length > 0) {
       return null;
    }

    return (
        <div className="min-h-screen h-screen bg-[var(--background)] text-[var(--text-primary)] flex flex-col font-sans overflow-hidden select-none">
            
            {/* ─── Proctoring Warning Modal (z-[9999], above EVERYTHING) ─── */}
            {warningVisible && (
                <ProctoringWarning 
                    count={warningDisplayCount} 
                    max={3} 
                    reason={warningReason} 
                    onDismiss={() => {
                        setWarningVisible(false);
                        proctoring.enterFullscreen();
                    }} 
                />
            )}

            {/* ─── Fullscreen Re-entry Banner ─── */}
            {!proctoring.isFullscreen && !warningVisible && (
                <div className="bg-red-500/10 border-b border-red-500/20 px-4 py-2.5 flex items-center justify-center gap-4 z-[100] shrink-0">
                    <span className="text-red-400 text-sm font-medium">⚠ You are not in fullscreen mode. Please re-enter to continue safely.</span>
                    <Button 
                        variant="secondary" 
                        size="sm" 
                        onClick={proctoring.enterFullscreen} 
                        className="h-7 text-xs bg-red-600/20 border-red-500/30 text-red-300 hover:bg-red-600/40"
                    >
                        <Maximize className="w-3 h-3 mr-1" /> Re-enter Fullscreen
                    </Button>
                </div>
            )}

            {/* ─── Top Header Bar ─── */}
            <header className="sticky top-0 z-50 bg-[var(--background)]/95 backdrop-blur-xl border-b border-[var(--border-subtle)] shrink-0">
                <div className="px-4 md:px-6 py-3 flex items-center justify-between gap-4">
                    {/* Left: Exam Name */}
                    <div className="flex items-center gap-3 min-w-0">
                        <h1 className="text-base font-bold text-[var(--text-primary)] tracking-tight truncate max-w-[200px] md:max-w-none">{exam.name}</h1>
                        <span className="hidden md:inline-flex text-[10px] uppercase tracking-wider text-[var(--text-dimmed)] bg-[var(--border-subtle)] px-2 py-0.5 rounded-md border border-[var(--border-default)] shrink-0">
                            {currentIndex + 1} / {questions.length}
                        </span>
                    </div>
                    
                    {/* Right: Timer, Sidebar Toggle, Submit */}
                    <div className="flex items-center gap-3">
                        <ExamTimer examId={examId as string} onTimeUp={handleSubmit} />
                        
                        {/* Sidebar toggle */}
                        <button
                            onClick={() => setSidebarOpen(!sidebarOpen)}
                            className="w-9 h-9 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-[var(--text-muted)] hover:text-white hover:bg-white/10 transition-all"
                            title={sidebarOpen ? "Hide question palette" : "Show question palette"}
                        >
                            {sidebarOpen ? <PanelRightClose className="w-4 h-4" /> : <PanelRightOpen className="w-4 h-4" />}
                        </button>

                        <Button 
                            variant="primary" 
                            className="bg-emerald-600 hover:bg-emerald-500 text-white border-none text-sm h-9 px-4"
                            onClick={() => {
                                if (hasUnanswered) {
                                    setShowConfirmSubmit(true);
                                } else {
                                    handleSubmit();
                                }
                            }}
                            disabled={submitting}
                        >
                            {submitting ? (
                                <span className="flex items-center gap-2">
                                    <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                                    Submitting
                                </span>
                            ) : (
                                <><Send className="w-3.5 h-3.5 mr-1.5" /> Submit</>
                            )}
                        </Button>
                    </div>
                </div>
            </header>

            {/* ─── Main Content Area ─── */}
            <div className="flex-1 flex overflow-hidden">
                
                {/* Left: Question Panel */}
                <div className={`flex-1 flex flex-col overflow-hidden transition-all duration-300 ${sidebarOpen ? 'mr-0' : 'mr-0'}`}>
                    {/* Question content - scrollable */}
                    <div className="flex-1 overflow-y-auto p-4 md:p-6" style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,0.1) transparent' }}>
                        <div className="max-w-4xl mx-auto">
                            {activeQuestion ? (
                                <AttemptQuestion question={activeQuestion} />
                            ) : (
                                <div className="flex-1 flex items-center justify-center bg-[var(--surface-1)] rounded-2xl border border-[var(--border-subtle)] min-h-[400px]">
                                    <p className="text-[var(--text-muted)]">No questions available.</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Bottom Navigation Bar - fixed at bottom */}
                    {activeQuestion && (
                        <div className="shrink-0 border-t border-[var(--border-subtle)] bg-[var(--background)]/95 backdrop-blur-xl px-4 md:px-6 py-3">
                            <div className="max-w-4xl mx-auto flex items-center justify-between">
                                <Button 
                                    variant="outline" 
                                    size="sm"
                                    onClick={goToPrev} 
                                    disabled={currentIndex <= 0}
                                    className="h-9"
                                >
                                    <ChevronLeft className="w-4 h-4 mr-1" /> Previous
                                </Button>

                                <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium text-[var(--text-muted)]">
                                        Q {currentIndex + 1} of {questions.length}
                                    </span>

                                    {/* Mobile palette toggle */}
                                    <button
                                        onClick={() => setSidebarOpen(!sidebarOpen)}
                                        className="lg:hidden w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400"
                                    >
                                        <PanelRightOpen className="w-4 h-4" />
                                    </button>
                                </div>

                                <Button 
                                    variant="outline" 
                                    size="sm"
                                    onClick={goToNext} 
                                    disabled={currentIndex >= questions.length - 1}
                                    className="h-9"
                                >
                                    Next <ChevronRight className="w-4 h-4 ml-1" />
                                </Button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Right: Sidebar / Question Palette */}
                {/* Desktop: slides in/out. Mobile: overlay */}
                <>
                    {/* Mobile overlay backdrop */}
                    {sidebarOpen && (
                        <div 
                            className="lg:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-[60]"
                            onClick={() => setSidebarOpen(false)}
                        />
                    )}

                    <aside className={`
                        ${sidebarOpen ? 'translate-x-0' : 'translate-x-full'}
                        fixed lg:relative right-0 top-0 h-full
                        w-[300px] lg:w-[320px]
                        bg-[var(--background)] lg:bg-transparent
                        border-l border-[var(--border-subtle)]
                        z-[70] lg:z-auto
                        transition-transform duration-300 ease-in-out
                        flex flex-col
                        ${!sidebarOpen ? 'lg:hidden' : ''}
                    `}>
                        {/* Mobile close button */}
                        <div className="lg:hidden flex items-center justify-between px-4 py-3 border-b border-white/[0.06]">
                            <span className="text-sm font-semibold text-white">Question Palette</span>
                            <button 
                                onClick={() => setSidebarOpen(false)}
                                className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-[var(--text-muted)] hover:text-white"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto p-4" style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,0.1) transparent' }}>
                            <AttemptSummary questions={questions} />
                        </div>
                    </aside>
                </>
            </div>

            {/* ─── Confirm Submit Modal ─── */}
            {showConfirmSubmit && (
                <div className="fixed inset-0 z-[9998] flex items-center justify-center bg-black/70 backdrop-blur-sm">
                    <div className="bg-[var(--surface-1)] border border-[var(--border-default)] rounded-2xl p-8 max-w-md w-full mx-4 space-y-6">
                        <div className="text-center space-y-3">
                            <div className="w-14 h-14 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mx-auto">
                                <AlertCircle className="w-7 h-7 text-amber-500" />
                            </div>
                            <h3 className="text-lg font-bold text-[var(--text-primary)]">Confirm Submission</h3>
                            <p className="text-[var(--text-muted)] text-sm">
                                You have <span className="text-amber-400 font-bold">{unansweredCount}</span> unanswered question{unansweredCount !== 1 ? 's' : ''}. 
                                Once submitted, you cannot change your answers.
                            </p>
                        </div>
                        <div className="flex gap-3">
                            <Button 
                                variant="outline" 
                                className="flex-1" 
                                onClick={() => setShowConfirmSubmit(false)}
                            >
                                Go Back
                            </Button>
                            <Button 
                                variant="primary" 
                                className="flex-1 bg-emerald-600 hover:bg-emerald-500 border-none"
                                onClick={handleSubmit}
                            >
                                <Send className="w-4 h-4 mr-2" /> Submit Anyway
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
