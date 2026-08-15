import React, { useState, useMemo } from "react";
import { QuestionCard } from "./QuestionCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { GlassCard } from "@/components/ui/glass-card";
import {
  PlusCircle,
  Trash2,
  Layers,
  HelpCircle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import type { QuestionUpsert, QuestionType } from "@/types";

interface SectionConfig {
  name: string; // "Section A", "Section B", etc.
  questionType: QuestionType;
  marksPerQuestion: number;
  description?: string;
}

interface QuestionListProps {
  questions: QuestionUpsert[];
  onChange: (questions: QuestionUpsert[]) => void;
}

const QUESTION_TYPES: { label: string; value: QuestionType }[] = [
  { label: "Multiple Choice (Single)", value: "MULTIPLE_CHOICE" },
  { label: "Multiple Select (Multiple)", value: "MULTIPLE_SELECT" },
  { label: "True / False", value: "TRUE_FALSE" },
  { label: "Short Answer", value: "SHORT_ANSWER" },
  { label: "Essay / Descriptive", value: "ESSAY" },
];

function getNextSectionLetter(existingNames: string[]): string {
  const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const usedLetters = new Set(
    existingNames
      .map((name) => {
        const match = name.match(/^Section ([A-Z])$/);
        return match ? match[1] : null;
      })
      .filter((l): l is string => Boolean(l))
  );

  for (let i = 0; i < letters.length; i++) {
    if (!usedLetters.has(letters[i])) {
      return `Section ${letters[i]}`;
    }
  }
  return `Section A`;
}

export function QuestionList({ questions, onChange }: QuestionListProps) {
  const [expandedQuestionKey, setExpandedQuestionKey] = useState<string | null>(
    null
  );
  const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({});

  // Derive active sections from questions or internal state
  const [sectionConfigs, setSectionConfigs] = useState<SectionConfig[]>(() => {
    const map = new Map<string, SectionConfig>();
    (questions || []).forEach((q) => {
      const secName = q.section?.trim() || "Section A";
      if (!map.has(secName)) {
        map.set(secName, {
          name: secName,
          questionType: q.questionType || "MULTIPLE_CHOICE",
          marksPerQuestion: q.marks || 1,
        });
      }
    });

    if (map.size === 0) {
      return [
        {
          name: "Section A",
          questionType: "MULTIPLE_CHOICE",
          marksPerQuestion: 1,
        },
      ];
    }
    return Array.from(map.values()).sort((a, b) => a.name.localeCompare(b.name));
  });

  // Group questions by section name
  const groupedQuestions = useMemo(() => {
    const map: Record<string, { questions: QuestionUpsert[]; globalIndices: number[] }> = {};
    sectionConfigs.forEach((sec) => {
      map[sec.name] = { questions: [], globalIndices: [] };
    });

    (questions || []).forEach((q, globalIdx) => {
      const secName = q.section || "Section A";
      if (!map[secName]) {
        map[secName] = { questions: [], globalIndices: [] };
      }
      map[secName].questions.push(q);
      map[secName].globalIndices.push(globalIdx);
    });

    return map;
  }, [questions, sectionConfigs]);

  // ── Section Actions ──────────────────────────────────────────────────────────

  const addSection = () => {
    const nextName = getNextSectionLetter(sectionConfigs.map((s) => s.name));
    const newConfig: SectionConfig = {
      name: nextName,
      questionType: "MULTIPLE_CHOICE",
      marksPerQuestion: 2,
    };
    setSectionConfigs((prev) => [...prev, newConfig]);
  };

  const removeSection = (sectionName: string) => {
    if (sectionConfigs.length <= 1) return;
    setSectionConfigs((prev) => prev.filter((s) => s.name !== sectionName));
    // Also remove questions belonging to this section and re-sequence question numbers
    const remainingQuestions = (questions || [])
      .filter((q) => q.section !== sectionName)
      .map((q, idx) => ({ ...q, questionNumber: idx + 1 }));
    onChange(remainingQuestions);
  };

  const updateSectionConfig = (
    sectionName: string,
    updates: Partial<SectionConfig>
  ) => {
    setSectionConfigs((prev) =>
      prev.map((s) => (s.name === sectionName ? { ...s, ...updates } : s))
    );

    // If questionType or marksPerQuestion changed, propagate to all questions in this section
    const newQuestions = (questions || []).map((q) => {
      if (q.section === sectionName) {
        const updatedType = updates.questionType ?? q.questionType;
        const updatedMarks = updates.marksPerQuestion ?? q.marks;
        let updatedOptions = q.options;

        if (updates.questionType) {
          if (updates.questionType === "TRUE_FALSE") {
            updatedOptions = [
              { text: "True", optionNumber: 1, isCorrect: true },
              { text: "False", optionNumber: 2, isCorrect: false },
            ];
          } else if (
            updates.questionType === "SHORT_ANSWER" ||
            updates.questionType === "ESSAY"
          ) {
            updatedOptions = [];
          }
        }

        return {
          ...q,
          questionType: updatedType,
          marks: updatedMarks,
          options: updatedOptions,
        };
      }
      return q;
    });

    onChange(newQuestions);
  };

  // ── Question Actions ─────────────────────────────────────────────────────────

  const addQuestionToSection = (section: SectionConfig) => {
    const newQuestion: QuestionUpsert = {
      text: "",
      marks: section.marksPerQuestion,
      questionNumber: (questions || []).length + 1,
      questionType: section.questionType,
      examId: "placeholder",
      section: section.name,
      options:
        section.questionType === "TRUE_FALSE"
          ? [
              { text: "True", optionNumber: 1, isCorrect: true },
              { text: "False", optionNumber: 2, isCorrect: false },
            ]
          : section.questionType === "SHORT_ANSWER" ||
            section.questionType === "ESSAY"
          ? []
          : [
              { text: "", optionNumber: 1, isCorrect: true },
              { text: "", optionNumber: 2, isCorrect: false },
              { text: "", optionNumber: 3, isCorrect: false },
              { text: "", optionNumber: 4, isCorrect: false },
            ],
    };

    const updated = [...(questions || []), newQuestion];
    // Re-sequence
    updated.forEach((q, idx) => {
      q.questionNumber = idx + 1;
    });
    onChange(updated);

    const questionKey = `${section.name}-${(groupedQuestions[section.name]?.questions.length || 0)}`;
    setExpandedQuestionKey(questionKey);
  };

  const updateQuestionByGlobalIndex = (
    globalIndex: number,
    updated: QuestionUpsert
  ) => {
    const copy = [...questions];
    copy[globalIndex] = updated;
    onChange(copy);
  };

  const deleteQuestionByGlobalIndex = (globalIndex: number) => {
    const filtered = questions.filter((_, idx) => idx !== globalIndex);
    filtered.forEach((q, idx) => {
      q.questionNumber = idx + 1;
    });
    onChange(filtered);
    setExpandedQuestionKey(null);
  };

  const toggleSectionCollapse = (sectionName: string) => {
    setCollapsedSections((prev) => ({
      ...prev,
      [sectionName]: !prev[sectionName],
    }));
  };

  const totalExamMarks = useMemo(
    () => (questions || []).reduce((sum, q) => sum + (q.marks || 0), 0),
    [questions]
  );

  return (
    <div className="space-y-8">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            <h2 className="text-xl font-bold text-[var(--text-primary)]">
              Exam Sections & Questions
            </h2>
          </div>
          <p className="text-[var(--text-muted)] text-sm mt-1">
            Exams are organized into strict sections (e.g. Section A, Section B).
            Each section enforces a fixed question type and marking scheme.
          </p>
        </div>

        <Button
          type="button"
          onClick={addSection}
          variant="secondary"
          size="sm"
          className="shrink-0"
        >
          <PlusCircle className="mr-2 h-4 w-4 text-indigo-400" />
          Add Next Section ({getNextSectionLetter(sectionConfigs.map((s) => s.name))})
        </Button>
      </div>

      {/* ── Sections Overview Strip ── */}
      <div className="flex flex-wrap items-center gap-2 bg-[var(--surface-1)] p-3 rounded-xl border border-[var(--border-subtle)]">
        <span className="text-xs font-semibold text-[var(--text-dimmed)] uppercase tracking-wider mr-2">
          Sections:
        </span>
        {sectionConfigs.map((sec) => {
          const qCount = groupedQuestions[sec.name]?.questions.length || 0;
          const secMarks = qCount * sec.marksPerQuestion;
          return (
            <div
              key={sec.name}
              className="flex items-center gap-2 bg-[var(--surface-2)] px-3 py-1.5 rounded-lg border border-[var(--border-subtle)] text-xs"
            >
              <span className="font-bold text-white">{sec.name}</span>
              <span className="text-[var(--text-muted)]">
                ({sec.questionType.replace(/_/g, " ")})
              </span>
              <Badge variant="default" className="text-[10px]">
                {sec.marksPerQuestion}M/Q
              </Badge>
              <Badge variant="neutral" className="text-[10px]">
                {qCount} Q ({secMarks} Marks)
              </Badge>
            </div>
          );
        })}
        <div className="ml-auto text-xs text-[var(--text-muted)]">
          Total: <strong className="text-white">{(questions || []).length}</strong> Questions •{" "}
          <strong className="text-emerald-400">{totalExamMarks}</strong> Marks
        </div>
      </div>

      {/* ── Sections List ── */}
      <div className="space-y-6">
        {sectionConfigs.map((sec) => {
          const secQuestions = groupedQuestions[sec.name]?.questions || [];
          const globalIndices = groupedQuestions[sec.name]?.globalIndices || [];
          const isCollapsed = collapsedSections[sec.name] || false;

          return (
            <GlassCard
              key={sec.name}
              padding="none"
              className="border-2 border-indigo-500/20 bg-[var(--surface-1)]/90 overflow-hidden shadow-lg"
            >
              {/* ── Section Configuration Header ── */}
              <div className="p-5 border-b border-[var(--border-subtle)] bg-gradient-to-r from-indigo-500/10 via-[var(--surface-2)] to-transparent">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center font-bold text-white text-base shrink-0">
                      {sec.name.replace("Section ", "")}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-bold text-white tracking-wide">
                          {sec.name}
                        </h3>
                        <Badge variant="success" className="text-[10px]">
                          Fixed Scheme
                        </Badge>
                      </div>
                      <p className="text-xs text-[var(--text-muted)]">
                        {secQuestions.length} {secQuestions.length === 1 ? "question" : "questions"} •{" "}
                        {secQuestions.length * sec.marksPerQuestion} marks total
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {sectionConfigs.length > 1 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeSection(sec.name)}
                        className="text-red-400 hover:bg-red-400/10 hover:text-red-300 h-8 px-2"
                        title={`Delete ${sec.name}`}
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        Delete Section
                      </Button>
                    )}
                    <button
                      type="button"
                      onClick={() => toggleSectionCollapse(sec.name)}
                      className="p-2 rounded-lg bg-[var(--surface-3)] text-[var(--text-muted)] hover:text-white transition-colors"
                      title={isCollapsed ? "Expand section" : "Collapse section"}
                    >
                      {isCollapsed ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronUp className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Section Parameters Row */}
                <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 mt-4 pt-4 border-t border-white/5">
                  <div className="sm:col-span-6 space-y-1">
                    <Label className="text-xs text-[var(--text-muted)] font-medium">
                      Fixed Question Type
                    </Label>
                    <Select
                      value={sec.questionType}
                      onChange={(e) =>
                        updateSectionConfig(sec.name, {
                          questionType: e.target.value as QuestionType,
                        })
                      }
                      className="bg-[var(--surface-2)] text-sm h-9"
                    >
                      {QUESTION_TYPES.map((t) => (
                        <option key={t.value} value={t.value}>
                          {t.label}
                        </option>
                      ))}
                    </Select>
                  </div>

                  <div className="sm:col-span-3 space-y-1">
                    <Label className="text-xs text-[var(--text-muted)] font-medium">
                      Marks Per Question
                    </Label>
                    <Input
                      type="number"
                      min="1"
                      value={sec.marksPerQuestion || ""}
                      onChange={(e) =>
                        updateSectionConfig(sec.name, {
                          marksPerQuestion: Math.max(1, parseInt(e.target.value) || 1),
                        })
                      }
                      className="bg-[var(--surface-2)] text-sm h-9"
                    />
                  </div>

                  <div className="sm:col-span-3 flex items-end">
                    <Button
                      type="button"
                      variant="primary"
                      size="sm"
                      onClick={() => addQuestionToSection(sec)}
                      className="w-full h-9 shadow-glow text-xs"
                    >
                      <PlusCircle className="mr-1.5 h-3.5 w-3.5" />
                      Add to {sec.name}
                    </Button>
                  </div>
                </div>
              </div>

              {/* ── Section Questions Body ── */}
              {!isCollapsed && (
                <div className="p-5 space-y-4 bg-[var(--surface-1)]">
                  {secQuestions.length === 0 ? (
                    <div className="p-8 text-center rounded-xl border border-dashed border-[var(--border-subtle)] bg-[var(--surface-2)]/50 space-y-3">
                      <HelpCircle className="w-8 h-8 text-[var(--text-dimmed)] mx-auto" />
                      <div className="space-y-1">
                        <p className="text-sm font-medium text-[var(--text-primary)]">
                          No questions in {sec.name} yet
                        </p>
                        <p className="text-xs text-[var(--text-muted)]">
                          Questions added here will automatically have{" "}
                          <strong className="text-white">{sec.marksPerQuestion} Marks</strong> and type{" "}
                          <strong className="text-white">
                            {sec.questionType.replace(/_/g, " ")}
                          </strong>
                          .
                        </p>
                      </div>
                      <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={() => addQuestionToSection(sec)}
                      >
                        <PlusCircle className="mr-1.5 h-4 w-4" /> Add First Question to {sec.name}
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {secQuestions.map((q, localIdx) => {
                        const globalIdx = globalIndices[localIdx];
                        const questionKey = `${sec.name}-${localIdx}`;
                        const isExpanded = expandedQuestionKey === questionKey;

                        return (
                          <QuestionCard
                            key={globalIdx}
                            index={globalIdx}
                            question={q}
                            isExpanded={isExpanded}
                            onToggleExpand={() =>
                              setExpandedQuestionKey(isExpanded ? null : questionKey)
                            }
                            onChange={(updated) =>
                              updateQuestionByGlobalIndex(globalIdx, {
                                ...updated,
                                section: sec.name,
                                questionType: sec.questionType,
                                marks: sec.marksPerQuestion,
                              })
                            }
                            onDelete={() => deleteQuestionByGlobalIndex(globalIdx)}
                            fixedType={sec.questionType}
                            fixedMarks={sec.marksPerQuestion}
                            sectionName={sec.name}
                          />
                        );
                      })}

                      <Button
                        type="button"
                        onClick={() => addQuestionToSection(sec)}
                        variant="outline"
                        size="sm"
                        className="w-full border-dashed border-[var(--border-subtle)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-indigo-500/40 mt-2"
                      >
                        <PlusCircle className="mr-2 h-4 w-4" /> Add Another Question to {sec.name}
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </GlassCard>
          );
        })}
      </div>
    </div>
  );
}
