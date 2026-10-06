"use client";

import React, { useState, useMemo } from "react";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  FileCheck2,
  HelpCircle,
  Plus,
  Save,
  Trash2,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type {
  AnswerKeyImport,
  MatchedAnswer,
  RubricCriterion,
} from "@/types/answer-key-import";
import type { Question } from "@/types/question";

interface AnswerKeyImportReviewProps {
  importData: AnswerKeyImport;
  examQuestions: Question[];
  onSaveDraft: (answers: MatchedAnswer[], title?: string) => Promise<void>;
  onConfirm: (overwriteExisting: boolean, answers: MatchedAnswer[]) => Promise<void>;
  onCancel: () => void;
  isConfirming: boolean;
  isSaving: boolean;
  error?: string | null;
}

export function AnswerKeyImportReview({
  importData,
  examQuestions,
  onSaveDraft,
  onConfirm,
  onCancel,
  isConfirming,
  isSaving,
  error,
}: AnswerKeyImportReviewProps) {
  const [answers, setAnswers] = useState<MatchedAnswer[]>(() => {
    return (importData.answers || []).map((a) => ({
      ...a,
      rubric: (a.rubric || []).map((r) => ({ ...r })),
      warnings: [...(a.warnings || [])],
      candidate_question_ids: [...(a.candidate_question_ids || [])],
    }));
  });

  const [docTitle, setDocTitle] = useState(importData.title || "");
  const [overwriteExisting, setOverwriteExisting] = useState(false);
  const [expandedIndices, setExpandedIndices] = useState<Record<number, boolean>>({});

  // ── Match statistics ───────────────────────────────────────────────────────
  const matchStats = useMemo(() => {
    let matched = 0;
    let ambiguous = 0;
    let unmatched = 0;

    answers.forEach((a) => {
      if (a.status === "MATCHED" && a.matched_question_id) matched++;
      else if (a.status === "AMBIGUOUS") ambiguous++;
      else unmatched++;
    });

    return {
      matched,
      ambiguous,
      unmatched,
      total: answers.length,
      canConfirm: matched > 0,
    };
  }, [answers]);

  // ── Mutators ──────────────────────────────────────────────────────────────
  const updateAnswer = (index: number, updates: Partial<MatchedAnswer>) => {
    setAnswers((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], ...updates };
      return next;
    });
  };

  const removeAnswer = (index: number) => {
    setAnswers((prev) => prev.filter((_, i) => i !== index));
  };

  const toggleExpand = (index: number) => {
    setExpandedIndices((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  // Assign an exam question to an answer
  const handleAssignQuestion = (index: number, questionId: string) => {
    if (!questionId) {
      updateAnswer(index, {
        matched_question_id: null,
        matched_question_number: null,
        matched_question_text: null,
        matched_question_type: null,
        matched_option_id: null,
        status: "UNMATCHED",
      });
      return;
    }

    const targetQ = examQuestions.find((q) => q.id === questionId);
    if (!targetQ) return;

    // Check if objective and attempt auto-mapping option
    let optId: string | null = null;
    const ans = answers[index];
    if (
      ["MULTIPLE_CHOICE", "TRUE_FALSE", "MULTIPLE_SELECT"].includes(
        targetQ.questionType
      ) &&
      targetQ.options
    ) {
      if (ans.selected_option) {
        const sel = ans.selected_option.trim().toUpperCase();
        if (sel === "TRUE" || sel === "T") {
          const opt = targetQ.options.find((o) =>
            o.text.trim().toLowerCase().startsWith("t")
          );
          if (opt) optId = opt.id;
        } else if (sel === "FALSE" || sel === "F") {
          const opt = targetQ.options.find((o) =>
            o.text.trim().toLowerCase().startsWith("f")
          );
          if (opt) optId = opt.id;
        } else {
          const letterMatch = sel.match(/([A-Z])/);
          if (letterMatch) {
            const idx = letterMatch[1].charCodeAt(0) - 65;
            if (idx >= 0 && idx < targetQ.options.length) {
              optId = targetQ.options[idx].id;
            }
          }
        }
      }
    }

    updateAnswer(index, {
      matched_question_id: targetQ.id,
      matched_question_number: targetQ.questionNumber,
      matched_question_text: targetQ.text,
      matched_question_type: targetQ.questionType,
      matched_option_id: optId || ans.matched_option_id,
      status: "MATCHED",
      match_reason: `Manually linked to Question #${targetQ.questionNumber}`,
    });
  };

  // Add a rubric criterion
  const addRubricCriterion = (ansIndex: number) => {
    setAnswers((prev) => {
      const next = [...prev];
      const curRubric = next[ansIndex].rubric || [];
      next[ansIndex].rubric = [
        ...curRubric,
        { criterion: "Criterion", marks: 1, description: "" },
      ];
      return next;
    });
  };

  const updateRubricCriterion = (
    ansIndex: number,
    critIndex: number,
    updates: Partial<RubricCriterion>
  ) => {
    setAnswers((prev) => {
      const next = [...prev];
      const curRubric = [...(next[ansIndex].rubric || [])];
      curRubric[critIndex] = { ...curRubric[critIndex], ...updates };
      next[ansIndex].rubric = curRubric;
      return next;
    });
  };

  const removeRubricCriterion = (ansIndex: number, critIndex: number) => {
    setAnswers((prev) => {
      const next = [...prev];
      next[ansIndex].rubric = next[ansIndex].rubric.filter((_, i) => i !== critIndex);
      return next;
    });
  };

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* ── Summary & Stats Header ────────────────────────────────────────── */}
      <GlassCard className="p-4 bg-white/70 dark:bg-zinc-900/70 border border-zinc-200 dark:border-zinc-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
              <FileCheck2 className="w-5 h-5 text-indigo-500" />
              Review Extracted Answer Key
            </h2>
            <div className="mt-2 flex items-center gap-2">
              <span className="text-xs font-medium text-zinc-500">Document Title:</span>
              <Input
                value={docTitle}
                onChange={(e) => setDocTitle(e.target.value)}
                placeholder="Answer key title..."
                className="h-7 text-xs max-w-xs"
              />
            </div>
            <p className="text-xs text-zinc-500 mt-1">
              Verify question associations, correct option selections, and marking rubrics before applying.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Badge
              variant="outline"
              className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
            >
              {matchStats.matched} Matched
            </Badge>
            {matchStats.ambiguous > 0 && (
              <Badge
                variant="outline"
                className="bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20"
              >
                {matchStats.ambiguous} Ambiguous
              </Badge>
            )}
            {matchStats.unmatched > 0 && (
              <Badge
                variant="outline"
                className="bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20"
              >
                {matchStats.unmatched} Unmatched
              </Badge>
            )}
            <Badge variant="secondary" className="bg-zinc-100 dark:bg-zinc-800">
              {matchStats.total} Total Items
            </Badge>
          </div>
        </div>

        {/* Overwrite Safety Toggle */}
        <div className="mt-4 pt-4 border-t border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
          <label className="flex items-center gap-2.5 cursor-pointer text-sm text-zinc-700 dark:text-zinc-300">
            <input
              type="checkbox"
              checked={overwriteExisting}
              onChange={(e) => setOverwriteExisting(e.target.checked)}
              className="h-4 w-4 rounded border-zinc-300 text-indigo-600 focus:ring-indigo-500"
            />
            <span className="font-medium">
              Overwrite existing question answers & rubrics
            </span>
          </label>
          <span className="text-xs text-zinc-500">
            {overwriteExisting
              ? "Existing correct answers on matched questions will be replaced."
              : "Existing correct answers on questions will be preserved."}
          </span>
        </div>
      </GlassCard>

      {/* ── Document-level Warnings ───────────────────────────────────────── */}
      {importData.warnings && importData.warnings.length > 0 && (
        <div className="p-3 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800/40 rounded-lg flex items-start gap-2 text-xs text-amber-800 dark:text-amber-300">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
          <ul className="list-disc list-inside space-y-0.5">
            {importData.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Action Error Display ─────────────────────────────────────────── */}
      {error && (
        <div className="p-3 bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-800/40 rounded-lg flex items-center gap-2 text-sm text-rose-700 dark:text-rose-300">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* ── Answers List ─────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1 max-h-[55vh]">
        {answers.length === 0 ? (
          <div className="text-center py-12 text-zinc-500">
            <HelpCircle className="w-8 h-8 mx-auto mb-2 text-zinc-400" />
            <p className="text-sm">No answers were detected in this document.</p>
          </div>
        ) : (
          answers.map((ans, idx) => {
            const isExpanded = expandedIndices[idx] !== false; // expanded by default
            const targetQ = examQuestions.find(
              (q) => q.id === ans.matched_question_id
            );

            return (
              <GlassCard
                key={idx}
                className={`p-4 border transition-all ${
                  ans.status === "MATCHED"
                    ? "border-emerald-500/30 bg-white/80 dark:bg-zinc-900/80"
                    : ans.status === "AMBIGUOUS"
                    ? "border-amber-500/30 bg-amber-50/20 dark:bg-amber-950/10"
                    : "border-zinc-300 dark:border-zinc-700 bg-zinc-50/30 dark:bg-zinc-900/30"
                }`}
              >
                {/* Header row */}
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                      Ref: {ans.question_reference || `#${idx + 1}`}
                    </span>

                    {/* Status Pill */}
                    {ans.status === "MATCHED" ? (
                      <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 text-xs">
                        <CheckCircle2 className="w-3 h-3 mr-1" />
                        Matched to Q#{ans.matched_question_number}
                      </Badge>
                    ) : ans.status === "AMBIGUOUS" ? (
                      <Badge className="bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 text-xs">
                        <AlertTriangle className="w-3 h-3 mr-1" />
                        Ambiguous
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-xs text-zinc-500">
                        Unmatched
                      </Badge>
                    )}

                    {ans.confidence && (
                      <Badge variant="secondary" className="text-[10px]">
                        {ans.confidence}
                      </Badge>
                    )}
                  </div>

                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleExpand(idx)}
                      className="h-7 w-7 p-0"
                    >
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeAnswer(idx)}
                      className="h-7 w-7 p-0 text-rose-500 hover:text-rose-600"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>

                {isExpanded && (
                  <div className="mt-3 space-y-3 pt-3 border-t border-zinc-200/60 dark:border-zinc-800/60">
                    {/* Question Matching Assignment Selector */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400 mb-1">
                          Exam Question Association
                        </label>
                        <select
                          className="w-full text-xs h-8 px-2 rounded-md border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800"
                          value={ans.matched_question_id || ""}
                          onChange={(e) => handleAssignQuestion(idx, e.target.value)}
                        >
                          <option value="">-- Select Question to Map --</option>
                          {examQuestions.map((q) => (
                            <option key={q.id} value={q.id}>
                              Q#{q.questionNumber}: {q.text.slice(0, 45)}... ({q.questionType})
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Objective Option Selector if applicable */}
                      {targetQ &&
                        ["MULTIPLE_CHOICE", "TRUE_FALSE", "MULTIPLE_SELECT"].includes(
                          targetQ.questionType
                        ) &&
                        targetQ.options && (
                          <div>
                            <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400 mb-1">
                              Correct Option
                            </label>
                            <select
                              className="w-full text-xs h-8 px-2 rounded-md border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800"
                              value={ans.matched_option_id || ""}
                              onChange={(e) =>
                                updateAnswer(idx, { matched_option_id: e.target.value })
                              }
                            >
                              <option value="">-- Select Option --</option>
                              {targetQ.options.map((opt) => (
                                <option key={opt.id} value={opt.id}>
                                  Opt {opt.optionNumber}: {opt.text}
                                </option>
                              ))}
                            </select>
                          </div>
                        )}
                    </div>

                    {/* Extracted snippet or raw value */}
                    {ans.selected_option && (
                      <div className="text-xs text-zinc-600 dark:text-zinc-400">
                        <span className="font-semibold text-zinc-700 dark:text-zinc-300">
                          Extracted Option:
                        </span>{" "}
                        <span className="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 font-mono">
                          {ans.selected_option}
                        </span>
                        {ans.selected_option_text && (
                          <span className="ml-1.5 italic">
                            ({ans.selected_option_text})
                          </span>
                        )}
                      </div>
                    )}

                    {/* Subjective Reference Answer */}
                    {(!targetQ ||
                      ["SHORT_ANSWER", "ESSAY"].includes(targetQ.questionType)) && (
                      <div>
                        <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400 mb-1">
                          Reference / Model Answer
                        </label>
                        <Textarea
                          value={ans.reference_answer || ""}
                          onChange={(e) =>
                            updateAnswer(idx, { reference_answer: e.target.value })
                          }
                          placeholder="Reference answer or expected solution points..."
                          className="text-xs min-h-[60px]"
                        />
                      </div>
                    )}

                    {/* Rubric Criteria Builder */}
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-xs font-medium text-zinc-600 dark:text-zinc-400">
                          Grading Rubric
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => addRubricCriterion(idx)}
                          className="h-6 px-2 text-[11px] text-indigo-600 dark:text-indigo-400"
                        >
                          <Plus className="w-3 h-3 mr-1" />
                          Add Step
                        </Button>
                      </div>

                      {ans.rubric && ans.rubric.length > 0 ? (
                        <div className="space-y-1.5 bg-zinc-50/50 dark:bg-zinc-900/50 p-2 rounded-md border border-zinc-200/50 dark:border-zinc-800/50">
                          {ans.rubric.map((r, rIdx) => (
                            <div key={rIdx} className="flex items-center gap-2">
                              <Input
                                value={r.criterion}
                                onChange={(e) =>
                                  updateRubricCriterion(idx, rIdx, {
                                    criterion: e.target.value,
                                  })
                                }
                                placeholder="Criterion step"
                                className="h-7 text-xs flex-1"
                              />
                              <Input
                                type="number"
                                step="0.5"
                                value={r.marks}
                                onChange={(e) =>
                                  updateRubricCriterion(idx, rIdx, {
                                    marks: parseFloat(e.target.value) || 0,
                                  })
                                }
                                placeholder="Marks"
                                className="h-7 text-xs w-20"
                              />
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => removeRubricCriterion(idx, rIdx)}
                                className="h-7 w-7 p-0 text-zinc-400 hover:text-rose-500"
                              >
                                <Trash2 className="w-3 h-3" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-[11px] text-zinc-400 italic">
                          No criteria specified.
                        </p>
                      )}
                    </div>

                    {/* Explanation */}
                    <div>
                      <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400 mb-1">
                        Explanation / Derivation
                      </label>
                      <Input
                        value={ans.explanation || ""}
                        onChange={(e) =>
                          updateAnswer(idx, { explanation: e.target.value })
                        }
                        placeholder="Explanation provided in answer key..."
                        className="text-xs h-8"
                      />
                    </div>

                    {/* Warnings */}
                    {ans.warnings && ans.warnings.length > 0 && (
                      <div className="text-[11px] text-amber-700 dark:text-amber-300 bg-amber-500/10 p-2 rounded border border-amber-500/20">
                        {ans.warnings.map((w, wIdx) => (
                          <div key={wIdx}>• {w}</div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </GlassCard>
            );
          })
        )}
      </div>

      {/* ── Footer Controls ─────────────────────────────────────────────── */}
      <div className="flex items-center justify-between pt-3 border-t border-zinc-200 dark:border-zinc-800">
        <Button variant="outline" size="sm" onClick={onCancel}>
          Cancel
        </Button>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onSaveDraft(answers, docTitle)}
            disabled={isSaving || isConfirming}
          >
            <Save className="w-4 h-4 mr-1.5" />
            {isSaving ? "Saving..." : "Save Draft"}
          </Button>

          <Button
            size="sm"
            onClick={() => onConfirm(overwriteExisting, answers)}
            disabled={!matchStats.canConfirm || isConfirming || isSaving}
            className="bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            <CheckCircle2 className="w-4 h-4 mr-1.5" />
            {isConfirming ? "Confirming..." : "Apply to Exam Questions"}
          </Button>
        </div>
      </div>
    </div>
  );
}
