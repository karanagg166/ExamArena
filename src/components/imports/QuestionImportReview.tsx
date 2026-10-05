"use client";

import React, { useState, useMemo } from "react";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  FileText,
  Plus,
  Save,
  Trash2,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type {
  ExtractedOption,
  ExtractedQuestion,
  QuestionImport,
} from "@/types/question-import";
import type { QuestionType } from "@/types/question";

interface QuestionImportReviewProps {
  importData: QuestionImport;
  onSaveDraft: (questions: ExtractedQuestion[], title?: string) => Promise<void>;
  onConfirm: () => Promise<void>;
  onCancel: () => void;
  isConfirming: boolean;
  isSaving: boolean;
  error?: string | null;
}

const QUESTION_TYPES: { label: string; value: QuestionType }[] = [
  { label: "Multiple Choice (Single)", value: "MULTIPLE_CHOICE" },
  { label: "Multiple Select (Multiple)", value: "MULTIPLE_SELECT" },
  { label: "True / False", value: "TRUE_FALSE" },
  { label: "Short Answer", value: "SHORT_ANSWER" },
  { label: "Essay / Descriptive", value: "ESSAY" },
];

export function QuestionImportReview({
  importData,
  onSaveDraft,
  onConfirm,
  onCancel,
  isConfirming,
  isSaving,
  error,
}: QuestionImportReviewProps) {
  const [questions, setQuestions] = useState<ExtractedQuestion[]>(() => {
    return (importData.questions || []).map((q) => ({
      ...q,
      options: (q.options || []).map((o) => ({ ...o })),
      warnings: [...(q.warnings || [])],
    }));
  });

  const paperTitle = importData.title || "";
  const [expandedIndices, setExpandedIndices] = useState<Record<number, boolean>>({});

  // ── Validation stats ──────────────────────────────────────────────────────
  const reviewStats = useMemo(() => {
    let unknownTypeCount = 0;
    let missingMarksCount = 0;
    let totalMarks = 0;

    questions.forEach((q) => {
      if (q.question_type === "UNKNOWN") unknownTypeCount++;
      if (q.marks === null || q.marks === undefined || q.marks <= 0) {
        missingMarksCount++;
      } else {
        totalMarks += Number(q.marks);
      }
    });

    const hasBlockingIssues = unknownTypeCount > 0 || missingMarksCount > 0;
    return {
      unknownTypeCount,
      missingMarksCount,
      totalMarks,
      hasBlockingIssues,
    };
  }, [questions]);

  // ── Mutators ─────────────────────────────────────────────────────────────
  const updateQuestion = (index: number, updates: Partial<ExtractedQuestion>) => {
    setQuestions((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], ...updates };
      return next;
    });
  };

  const removeQuestion = (index: number) => {
    setQuestions((prev) => prev.filter((_, i) => i !== index));
  };

  const addQuestion = () => {
    const newQ: ExtractedQuestion = {
      question_number: String(questions.length + 1),
      question_type: "MULTIPLE_CHOICE",
      text: "",
      marks: 1,
      section: "Section A",
      confidence: "HIGH",
      warnings: [],
      options: [
        { label: "A", text: "", is_correct: null },
        { label: "B", text: "", is_correct: null },
      ],
    };
    setQuestions((prev) => [...prev, newQ]);
    setExpandedIndices((prev) => ({ ...prev, [questions.length]: true }));
  };

  const updateOption = (
    qIndex: number,
    optIndex: number,
    updates: Partial<ExtractedOption>
  ) => {
    setQuestions((prev) => {
      const next = [...prev];
      const q = { ...next[qIndex] };
      const opts = [...q.options];
      opts[optIndex] = { ...opts[optIndex], ...updates };
      q.options = opts;
      next[qIndex] = q;
      return next;
    });
  };

  const addOption = (qIndex: number) => {
    setQuestions((prev) => {
      const next = [...prev];
      const q = { ...next[qIndex] };
      const opts = [...q.options];
      const nextLabel = String.fromCharCode(65 + opts.length); // A, B, C, D...
      opts.push({ label: nextLabel, text: "", is_correct: null });
      q.options = opts;
      next[qIndex] = q;
      return next;
    });
  };

  const removeOption = (qIndex: number, optIndex: number) => {
    setQuestions((prev) => {
      const next = [...prev];
      const q = { ...next[qIndex] };
      q.options = q.options.filter((_, i) => i !== optIndex);
      next[qIndex] = q;
      return next;
    });
  };

  const toggleExpand = (index: number) => {
    setExpandedIndices((prev) => ({ ...prev, [index]: !prev[index] }));
  };

  return (
    <div className="space-y-6">
      {/* ── Paper Summary Bar ────────────────────────────────────────────── */}
      <GlassCard padding="md" className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-400" />
              <h3 className="text-lg font-bold text-white">
                {paperTitle || importData.originalFileName}
              </h3>
            </div>
            <p className="text-xs text-[var(--text-muted)]">
              File: {importData.originalFileName} ({(importData.fileSize / 1024).toFixed(1)} KB)
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="px-3 py-1">
              {questions.length} Questions Detected
            </Badge>
            <Badge variant="neutral" className="px-3 py-1">
              Total: {reviewStats.totalMarks} Marks
            </Badge>
          </div>
        </div>

        {/* ── Blocking Warnings Banner ── */}
        {reviewStats.hasBlockingIssues && (
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 space-y-2">
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              Action required before confirming import:
            </div>
            <ul className="text-xs text-amber-300/90 list-disc list-inside space-y-1">
              {reviewStats.unknownTypeCount > 0 && (
                <li>
                  {reviewStats.unknownTypeCount} question(s) have UNKNOWN type. Please assign a valid question type.
                </li>
              )}
              {reviewStats.missingMarksCount > 0 && (
                <li>
                  {reviewStats.missingMarksCount} question(s) have missing marks. Please specify marks.
                </li>
              )}
            </ul>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </GlassCard>

      {/* ── Extracted Questions List ─────────────────────────────────────── */}
      <div className="space-y-4">
        {questions.map((q, idx) => {
          const isExpanded = expandedIndices[idx] !== false; // expanded by default
          const isObjective = [
            "MULTIPLE_CHOICE",
            "MULTIPLE_SELECT",
            "TRUE_FALSE",
          ].includes(q.question_type);
          const hasMissingMarks = q.marks === null || q.marks === undefined || q.marks <= 0;
          const isUnknown = q.question_type === "UNKNOWN";

          return (
            <GlassCard
              key={idx}
              padding="md"
              className={`space-y-4 border transition-all ${
                isUnknown || hasMissingMarks
                  ? "border-amber-500/40 bg-amber-500/5"
                  : "border-[var(--border-subtle)]"
              }`}
            >
              {/* Question Header */}
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-bold text-white text-sm bg-[var(--surface-3)] px-2.5 py-1 rounded-lg">
                    Q{q.question_number || idx + 1}
                  </span>

                  {isUnknown ? (
                    <Badge variant="destructive" className="text-xs">
                      UNKNOWN TYPE ⚠
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-xs">
                      {q.question_type.replace(/_/g, " ")}
                    </Badge>
                  )}

                  {hasMissingMarks ? (
                    <Badge variant="warning" className="text-xs">
                      Missing Marks ⚠
                    </Badge>
                  ) : (
                    <span className="text-xs font-semibold text-zinc-300">
                      {q.marks} Marks
                    </span>
                  )}

                  <Badge
                    variant={
                      q.confidence === "HIGH"
                        ? "success"
                        : q.confidence === "MEDIUM"
                        ? "warning"
                        : "neutral"
                    }
                    className="text-[10px]"
                  >
                    {q.confidence} CONFIDENCE
                  </Badge>

                  {q.section && (
                    <span className="text-xs text-[var(--text-dimmed)]">
                      [{q.section}]
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleExpand(idx)}
                    className="h-8 w-8 p-0"
                    aria-label="Toggle details"
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
                    onClick={() => removeQuestion(idx)}
                    className="h-8 w-8 p-0 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                    aria-label="Delete question"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Question Warnings if any */}
              {q.warnings && q.warnings.length > 0 && (
                <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300">
                  {q.warnings.join("; ")}
                </div>
              )}

              {/* Editable Fields */}
              {isExpanded && (
                <div className="space-y-4 pt-2 border-t border-[var(--border-subtle)]">
                  {/* Meta Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                    <div>
                      <label className="text-[11px] font-semibold text-[var(--text-dimmed)] uppercase">
                        Question #
                      </label>
                      <Input
                        value={q.question_number || ""}
                        onChange={(e) =>
                          updateQuestion(idx, { question_number: e.target.value })
                        }
                        className="h-8 text-xs mt-1"
                        placeholder="1, 1(a), etc."
                      />
                    </div>

                    <div>
                      <label className="text-[11px] font-semibold text-[var(--text-dimmed)] uppercase">
                        Type
                      </label>
                      <Select
                        value={q.question_type}
                        onChange={(e) =>
                          updateQuestion(idx, {
                            question_type: e.target.value as QuestionType,
                          })
                        }
                        className="h-8 text-xs mt-1"
                      >
                        {isUnknown && (
                          <option value="UNKNOWN">-- Select Type --</option>
                        )}
                        {QUESTION_TYPES.map((t) => (
                          <option key={t.value} value={t.value}>
                            {t.label}
                          </option>
                        ))}
                      </Select>
                    </div>

                    <div>
                      <label className="text-[11px] font-semibold text-[var(--text-dimmed)] uppercase">
                        Marks
                      </label>
                      <Input
                        type="number"
                        min="1"
                        value={q.marks ?? ""}
                        onChange={(e) =>
                          updateQuestion(idx, {
                            marks: e.target.value ? Number(e.target.value) : null,
                          })
                        }
                        className={`h-8 text-xs mt-1 ${
                          hasMissingMarks ? "border-amber-500 ring-1 ring-amber-500" : ""
                        }`}
                        placeholder="Marks (e.g. 2)"
                      />
                    </div>

                    <div>
                      <label className="text-[11px] font-semibold text-[var(--text-dimmed)] uppercase">
                        Section
                      </label>
                      <Input
                        value={q.section || ""}
                        onChange={(e) =>
                          updateQuestion(idx, { section: e.target.value })
                        }
                        className="h-8 text-xs mt-1"
                        placeholder="e.g. Section A"
                      />
                    </div>
                  </div>

                  {/* Question Text */}
                  <div>
                    <label className="text-[11px] font-semibold text-[var(--text-dimmed)] uppercase">
                      Question Text
                    </label>
                    <Textarea
                      rows={2}
                      value={q.text}
                      onChange={(e) => updateQuestion(idx, { text: e.target.value })}
                      className="text-sm mt-1"
                      placeholder="Enter question wording..."
                    />
                  </div>

                  {/* Options (for objective questions) */}
                  {isObjective && (
                    <div className="space-y-2 pt-2">
                      <div className="flex items-center justify-between">
                        <label className="text-[11px] font-semibold text-[var(--text-dimmed)] uppercase">
                          Answer Options
                        </label>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => addOption(idx)}
                          className="h-7 text-xs text-indigo-400 hover:text-indigo-300"
                        >
                          <Plus className="w-3.5 h-3.5 mr-1" /> Add Option
                        </Button>
                      </div>

                      <div className="space-y-2">
                        {q.options.map((opt, optIdx) => (
                          <div key={optIdx} className="flex items-center gap-2">
                            <span className="w-7 text-center font-bold text-xs text-zinc-400 bg-[var(--surface-2)] py-1.5 rounded-lg border border-[var(--border-subtle)] shrink-0">
                              {opt.label || String.fromCharCode(65 + optIdx)}
                            </span>
                            <Input
                              value={opt.text}
                              onChange={(e) =>
                                updateOption(idx, optIdx, { text: e.target.value })
                              }
                              className="h-8 text-xs flex-1"
                              placeholder={`Option ${opt.label || optIdx + 1}`}
                            />
                            {q.options.length > 2 && (
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                onClick={() => removeOption(idx, optIdx)}
                                className="h-8 w-8 p-0 text-zinc-500 hover:text-red-400"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </Button>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </GlassCard>
          );
        })}

        <Button
          type="button"
          variant="outline"
          onClick={addQuestion}
          className="w-full border-dashed border-[var(--border-subtle)] text-[var(--text-muted)] hover:text-white"
        >
          <Plus className="w-4 h-4 mr-2" /> Add Question to Paper
        </Button>
      </div>

      {/* ── Footer Actions ───────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-[var(--border-subtle)]">
        <Button variant="ghost" onClick={onCancel} disabled={isConfirming || isSaving}>
          Cancel
        </Button>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            onClick={() => onSaveDraft(questions, paperTitle)}
            disabled={isSaving || isConfirming}
          >
            <Save className="w-4 h-4 mr-2" />
            {isSaving ? "Saving Draft..." : "Save Draft"}
          </Button>

          <Button
            variant="primary"
            onClick={onConfirm}
            disabled={isConfirming || isSaving || reviewStats.hasBlockingIssues}
            className="shadow-glow"
          >
            <CheckCircle2 className="w-4 h-4 mr-2" />
            {isConfirming ? "Confirming Import..." : "Confirm Import"}
          </Button>
        </div>
      </div>
    </div>
  );
}
