"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Sparkles,
  CheckCircle2,
  Clock,
  Bot,
  AlertCircle,
  HelpCircle,
  Info,
} from "lucide-react";

import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/loading";
import { gradingApi } from "@/lib/api/grading";
import { gradingError } from "./status";
import type { ExamGradingSummary, BulkAIEvaluateResponse } from "@/types/grading";

interface BulkGradingCardProps {
  examId: string;
  onGradingEvaluated?: () => void;
}

export function BulkGradingCard({ examId, onGradingEvaluated }: BulkGradingCardProps) {
  const [summary, setSummary] = useState<ExamGradingSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [lastResult, setLastResult] = useState<BulkAIEvaluateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = useCallback(async () => {
    try {
      const data = await gradingApi.getExamGradingSummary(examId);
      setSummary(data);
      setError(null);
    } catch (err: unknown) {
      setError(gradingError(err));
    } finally {
      setLoading(false);
    }
  }, [examId]);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  const handleStartBulkEvaluation = async () => {
    setShowConfirm(false);
    setEvaluating(true);
    setError(null);
    try {
      const result = await gradingApi.bulkEvaluatePendingAnswers(examId, {
        limit: 20,
        regenerateExisting: false,
      });
      setLastResult(result);
      await fetchSummary();
      onGradingEvaluated?.();
    } catch (err: unknown) {
      setError(gradingError(err, true));
    } finally {
      setEvaluating(false);
    }
  };

  if (loading) {
    return (
      <GlassCard padding="md" className="space-y-3">
        <div className="flex items-center gap-3 text-slate-400">
          <Spinner className="h-4 w-4 text-indigo-500" />
          <span className="text-xs font-semibold">Loading subjective grading summary...</span>
        </div>
      </GlassCard>
    );
  }

  if (error && !summary) {
    return (
      <GlassCard padding="md" className="space-y-3 border-red-500/20 bg-red-500/5">
        <div className="flex items-center gap-2 text-red-500 text-sm">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
        <Button variant="outline" size="sm" onClick={fetchSummary}>
          Retry
        </Button>
      </GlassCard>
    );
  }

  if (!summary || summary.totalSubjectiveAnswers === 0) {
    return (
      <GlassCard padding="md" className="flex items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
              Subjective Grading
            </h3>
            <Badge variant="secondary">0 subjective answers</Badge>
          </div>
          <p className="text-xs text-slate-500">
            No subjective answers require grading. All questions in this exam are objective or auto-graded.
          </p>
        </div>
      </GlassCard>
    );
  }

  return (
    <GlassCard padding="lg" className="space-y-5 border-indigo-500/20">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
              Subjective Grading
            </h3>
            <Badge variant="info">
              {summary.totalSubjectiveAnswers} total subjective {summary.totalSubjectiveAnswers === 1 ? "answer" : "answers"}
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Generate draft AI grading suggestions for submitted short answers and essays. Teacher review remains mandatory.
          </p>
        </div>

        {summary.pending > 0 && !showConfirm && (
          <Button
            size="sm"
            onClick={() => setShowConfirm(true)}
            disabled={evaluating}
            className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm flex items-center gap-2 shrink-0"
          >
            {evaluating ? (
              <>
                <Spinner className="h-4 w-4 border-2" />
                <span>Evaluating pending subjective answers...</span>
              </>
            ) : (
              <>
                <Sparkles size={15} />
                <span>Evaluate Pending with AI</span>
              </>
            )}
          </Button>
        )}
      </div>

      {/* Confirmation Modal / Inline Callout */}
      {showConfirm && (
        <div className="rounded-xl border border-indigo-200 dark:border-indigo-900/60 bg-indigo-50/60 dark:bg-indigo-950/30 p-4 space-y-3 animate-fade-in">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-indigo-600 dark:text-indigo-400 mt-0.5 shrink-0" />
            <div className="space-y-1">
              <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                Confirm AI Evaluation Batch
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-300">
                Generate AI grading suggestions for up to 20 pending subjective answers? No marks will be finalized automatically. All suggestions are saved as drafts for teacher review.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 sm:justify-end pt-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowConfirm(false)}
              disabled={evaluating}
            >
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleStartBulkEvaluation}
              disabled={evaluating}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              Start AI Evaluation
            </Button>
          </div>
        </div>
      )}

      {/* Batch Result Notice */}
      {lastResult && (
        <div className="rounded-xl border border-emerald-200 dark:border-emerald-900/50 bg-emerald-50/50 dark:bg-emerald-950/20 p-3.5 space-y-1.5 animate-fade-in">
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-800 dark:text-emerald-300">
            <CheckCircle2 size={15} className="text-emerald-600 dark:text-emerald-400" />
            <span>
              {lastResult.processedCount} AI grading {lastResult.processedCount === 1 ? "suggestion" : "suggestions"} created.
            </span>
          </div>
          <div className="text-xs text-slate-600 dark:text-slate-300 flex flex-wrap gap-x-4 gap-y-1 pl-6">
            {lastResult.failedCount > 0 && (
              <span className="text-amber-600 dark:text-amber-400">
                {lastResult.failedCount} {lastResult.failedCount === 1 ? "answer" : "answers"} could not be evaluated.
              </span>
            )}
            <span>
              {lastResult.remainingCount} {lastResult.remainingCount === 1 ? "answer remains" : "answers remain"} pending.
            </span>
          </div>
        </div>
      )}

      {/* Error Notice */}
      {error && (
        <div className="rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50/50 dark:bg-red-950/20 p-3 flex items-center gap-2 text-xs text-red-600 dark:text-red-400">
          <AlertCircle size={15} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Stats Counter Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white/50 dark:bg-slate-900/40 p-3.5 space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Total</span>
            <HelpCircle size={15} className="text-slate-400" />
          </div>
          <p className="text-xl font-bold text-slate-800 dark:text-slate-200">
            {summary.totalSubjectiveAnswers}
          </p>
          <p className="text-[11px] text-slate-400">Subjective answers</p>
        </div>

        <div className="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white/50 dark:bg-slate-900/40 p-3.5 space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Pending</span>
            <Clock size={15} className="text-amber-500" />
          </div>
          <p className="text-xl font-bold text-amber-600 dark:text-amber-400">
            {summary.pending}
          </p>
          <p className="text-[11px] text-slate-400">Awaiting AI evaluation</p>
        </div>

        <div className="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white/50 dark:bg-slate-900/40 p-3.5 space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-semibold uppercase tracking-wider">AI Suggestions</span>
            <Bot size={15} className="text-indigo-500" />
          </div>
          <p className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
            {summary.aiSuggestionsReady}
          </p>
          <p className="text-[11px] text-slate-400">Draft suggestions ready</p>
        </div>

        <div className="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white/50 dark:bg-slate-900/40 p-3.5 space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Teacher Graded</span>
            <CheckCircle2 size={15} className="text-emerald-500" />
          </div>
          <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400">
            {summary.teacherGraded}
          </p>
          <p className="text-[11px] text-slate-400">Final marks approved</p>
        </div>
      </div>
    </GlassCard>
  );
}
