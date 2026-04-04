"use client";

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { GlassCard } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { useAttemptEngine } from '@/hooks/useAttemptEngine';
import { CheckCircle2, ArrowRight } from 'lucide-react';

export default function ExamResultPage() {
    const { examId } = useParams();
    const router = useRouter();
    const { clearAttempt, attemptId } = useAttemptEngine();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        // Ensure state is cleared so user can't resume
        if (attemptId) {
            clearAttempt();
        }
    }, [attemptId, clearAttempt]);

    if (!mounted) return null;

    return (
        <div className="page-shell flex items-center justify-center min-h-[80vh]">
            <GlassCard className="max-w-lg w-full p-12 text-center space-y-8 animate-fade-in mx-4">
                <div className="w-24 h-24 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-6 ring-4 ring-green-500/20">
                    <CheckCircle2 className="w-12 h-12 text-green-500" />
                </div>
                
                <div className="space-y-4">
                    <h2 className="text-3xl font-bold text-white tracking-tight">Exam Submitted</h2>
                    <p className="text-[var(--text-muted)] text-base leading-relaxed">
                        Your answers have been securely saved. Depending on the exam configuration, your teacher will review your submission or grades will be calculated automatically.
                    </p>
                </div>

                <div className="pt-8 border-t border-[var(--border-subtle)]">
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
        </div>
    );
}
