"use client";

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { PageHeader } from '@/components/ui/page-header';
import { GlassCard } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { api } from '@/lib/axios';
import { AlertCircle, Clock, FileText, CheckCircle2 } from 'lucide-react';
import { useAttemptEngine } from '@/hooks/useAttemptEngine';
import { getErrorMessage } from '@/lib/error';
import type { Exam } from '@/types';

export default function ExamStartPage() {
  const { examId } = useParams();
  const router = useRouter();
  const [exam, setExam] = useState<Exam | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [examCodeInput, setExamCodeInput] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { initializeAttempt } = useAttemptEngine();

  useEffect(() => {
    const fetchExam = async () => {
      try {
        const res = await api.get(`/api/v1/exams/${examId}`);
        setExam(res.data);
      } catch {
        setError("Failed to load exam details. It may not exist or not be published.");
      } finally {
        setLoading(false);
      }
    };
    if (examId) fetchExam();
  }, [examId]);

  const handleStart = async () => {
    if (!accepted) return;
    if (exam && exam.isPublic === false && !examCodeInput.trim()) {
      setError("Please enter the secret exam code provided by your teacher.");
      return;
    }
    
    setStarting(true);
    setError(null);
    try {
      // Create attempt backend side with optional examCode
      const res = await api.post('/api/v1/attempts/start', {
        examId,
        examCode: examCodeInput.trim().toUpperCase() || undefined,
      });
      const attemptData = res.data; // StudentExamResponse

      // Initialize local state
      initializeAttempt(
         examId as string, 
         attemptData.id, 
         attemptData.answers, 
         attemptData.startedAt,
         exam?.duration ? exam.duration * 60 : undefined // Assuming duration is in minutes in DB
      );

      // Force full screen
      try {
          if (document.documentElement.requestFullscreen) {
              await document.documentElement.requestFullscreen();
          }
      } catch (fsErr) {
          console.warn("Fullscreen request failed", fsErr);
      }

      router.push(`/student/exams/${examId}/attempt`);
    } catch (err: unknown) {
        setError(getErrorMessage(err) || "Failed to start the exam. You might have already submitted it.");
        setStarting(false);
    }
  };

  if (loading) {
    return (
      <div className="page-shell flex items-center justify-center min-h-[60vh]">
          <div className="w-10 h-10 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !exam) {
    return (
      <div className="page-shell">
        <GlassCard className="max-w-2xl mx-auto p-12 text-center space-y-6">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto" />
          <h2 className="text-2xl font-bold text-white">Oops</h2>
          <p className="text-[var(--text-muted)]">{error}</p>
          <Button onClick={() => router.push('/student/exams')}>Back to Exams</Button>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="page-shell">
      <div className="max-w-3xl mx-auto space-y-8 animate-fade-in relative z-10">
        <PageHeader 
            overline="Read Instructions Carefully"
            title={exam.name}
        />

        <GlassCard padding="lg" className="space-y-6">
           <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-1)]">
               <div>
                   <p className="text-xs text-[var(--text-dimmed)] uppercase mb-1">Duration</p>
                   <p className="text-white font-medium flex items-center gap-2"><Clock className="w-4 h-4 text-indigo-400"/> {exam.duration} mins</p>
               </div>
               <div>
                   <p className="text-xs text-[var(--text-dimmed)] uppercase mb-1">Max Marks</p>
                   <p className="text-white font-medium">{exam.maxMarks}</p>
               </div>
               <div>
                   <p className="text-xs text-[var(--text-dimmed)] uppercase mb-1">Questions</p>
                   <p className="text-white font-medium">{exam.questions?.length ?? 0}</p>
               </div>
                <div>
                   <p className="text-xs text-[var(--text-dimmed)] uppercase mb-1">Type</p>
                   <p className="text-white font-medium">{exam.type}</p>
               </div>
           </div>

           {/* Negative Marking & Access Info */}
           <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
             <div className="p-3.5 rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-1)]">
               <p className="text-xs text-[var(--text-dimmed)] uppercase font-semibold">Marking Policy</p>
               <p className="text-sm font-medium text-white mt-0.5">
                 {exam.negativeMarking ? (
                   <span className="text-amber-400">⚠️ Negative Marking Enabled (-{exam.negativeMarks} per wrong answer)</span>
                 ) : (
                   <span className="text-emerald-400">✅ No Negative Marking (0 for wrong answers)</span>
                 )}
               </p>
             </div>
             <div className="p-3.5 rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-1)]">
               <p className="text-xs text-[var(--text-dimmed)] uppercase font-semibold">Access Policy</p>
               <p className="text-sm font-medium text-white mt-0.5">
                 {exam.isPublic !== false ? (
                   <span className="text-emerald-400">🌐 Public Exam (Open to school students)</span>
                 ) : (
                   <span className="text-amber-400">🔒 Code-Protected Exam</span>
                 )}
               </p>
             </div>
           </div>

           {exam.isPublic === false && (
             <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 space-y-2">
               <label htmlFor="exam-code-input" className="text-xs font-semibold uppercase tracking-wider text-amber-300">
                 Enter Exam Access Password to Begin
               </label>
               <input
                 id="exam-code-input"
                 type="password"
                 placeholder="Enter secret access password..."
                 value={examCodeInput}
                 onChange={(e) => setExamCodeInput(e.target.value)}
                 className="w-full h-11 bg-zinc-900 border border-amber-500/40 rounded-xl px-4 text-base tracking-wider text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
               />
               <p className="text-xs text-zinc-400">
                 This private exam requires a secret access password provided by your teacher.
               </p>
             </div>
           )}

           <div className="space-y-4">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <FileText className="w-5 h-5 text-indigo-500" /> Instructions
              </h3>
              <div className="p-4 rounded-xl bg-[var(--surface-2)] border border-[var(--border-subtle)] text-[var(--text-muted)] text-sm leading-relaxed whitespace-pre-wrap min-h-[150px]">
                  {exam.instructions || "No specific instructions provided by the teacher. Please answer all questions to the best of your ability."}
              </div>
           </div>

           <div className="space-y-3 pt-6 border-t border-[var(--border-subtle)]">
               <h4 className="text-sm font-semibold text-white">Exam Conditions</h4>
               <ul className="space-y-2 text-sm text-[var(--text-muted)]">
                   <li className="flex gap-2 items-start"><CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 shrink-0"/> The exam will run in full-screen mode.</li>
                   <li className="flex gap-2 items-start"><CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 shrink-0"/> If you leave the window or switch tabs, your actions might be recorded as a violation.</li>
                   <li className="flex gap-2 items-start"><CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 shrink-0"/> The exam will automatically submit when the timer reaches zero.</li>
                   <li className="flex gap-2 items-start"><CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 shrink-0"/> Ensure you have a stable internet connection before starting. Local backups are kept, but submission requires network.</li>
               </ul>
           </div>

           {error && (
             <div className="p-3.5 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-sm">
               {error}
             </div>
           )}

           <div className="pt-6 mt-4">
               <label className="flex items-start gap-3 p-4 rounded-xl border-2 border-indigo-500/30 bg-indigo-500/5 cursor-pointer hover:bg-indigo-500/10 transition-colors">
                   <Checkbox 
                       checked={accepted} 
                       onCheckedChange={(c: boolean | 'indeterminate') => setAccepted(c === true)} 
                       className="mt-1 flex-shrink-0"
                   />
                   <span className="text-sm text-indigo-100 leading-relaxed font-medium">
                       I have read and understood all the instructions. I agree to abide by the exam conditions and maintain academic integrity.
                   </span>
               </label>
           </div>

           <div className="pt-4 flex justify-end gap-4">
               <Button variant="ghost" onClick={() => router.push('/student/exams')} disabled={starting}>
                   Cancel
               </Button>
               <Button 
                   variant="primary" 
                   size="lg" 
                   className="shadow-glow min-w-[150px]" 
                   disabled={!accepted || starting}
                   onClick={handleStart}
               >
                   {starting ? (
                       <span className="flex items-center gap-2">
                           <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span> Starting
                       </span>
                   ) : "Begin Exam"}
               </Button>
           </div>
        </GlassCard>
      </div>
    </div>
  );
}
