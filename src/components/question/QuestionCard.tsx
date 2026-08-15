import React from "react";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { ChevronDown, ChevronUp, Trash2 } from "lucide-react";
import { QuestionOptions } from "./QuestionOptions";
import type { QuestionUpsert, QuestionType } from "@/types";
import { cn } from "@/lib/utils";

interface QuestionCardProps {
  question: QuestionUpsert;
  index: number;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onChange: (updated: QuestionUpsert) => void;
  onDelete: () => void;
  fixedType?: QuestionType;
  fixedMarks?: number;
  sectionName?: string;
}

export function QuestionCard({
  question,
  index,
  isExpanded,
  onToggleExpand,
  onChange,
  onDelete,
  fixedType,
  fixedMarks,
  sectionName,
}: QuestionCardProps) {
  const updateField = <K extends keyof QuestionUpsert>(
    field: K,
    value: QuestionUpsert[K]
  ) => {
    onChange({ ...question, [field]: value });
  };

  const currentType = fixedType || question.questionType;
  const currentMarks = fixedMarks ?? question.marks;
  const currentSection = sectionName || question.section;

  return (
    <GlassCard
      padding="none"
      className="overflow-hidden transition-smooth border border-[var(--border-default)]"
    >
      {/* ─── Compact Header (Always visible) ─── */}
      <div
        className={cn(
          "flex items-center gap-3 p-4 cursor-pointer hover:bg-[var(--surface-2)] transition-colors",
          isExpanded
            ? "border-b border-[var(--border-subtle)] bg-[var(--surface-2)]"
            : ""
        )}
        onClick={onToggleExpand}
      >
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-[var(--surface-3)] text-sm font-semibold text-[var(--accent)] shrink-0">
          {index + 1}
        </div>

        <div className="flex-grow flex flex-col sm:flex-row gap-2 sm:items-center justify-between">
          <p className="text-sm font-medium text-[var(--text-primary)] line-clamp-1 truncate pe-4">
            {question.text || (
              <span className="text-[var(--text-dimmed)] italic">
                Empty Question prompt...
              </span>
            )}
          </p>

          <div className="flex items-center gap-2 shrink-0">
            {currentSection && (
              <Badge variant="neutral" className="text-[10px]">
                {currentSection}
              </Badge>
            )}
            <Badge variant="neutral" className="text-[10px] hidden sm:inline-flex">
              {currentType.replace(/_/g, " ")}
            </Badge>
            <Badge variant="default" className="text-[10px]">
              {currentMarks} {currentMarks === 1 ? "Mark" : "Marks"}
            </Badge>
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0 ml-2">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="p-1.5 text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
            title="Delete Question"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <div className="p-1.5 text-[var(--text-muted)]">
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </div>
        </div>
      </div>

      {/* ─── Expanded Body Editor ─── */}
      {isExpanded && (
        <div className="p-5 md:p-6 space-y-6 animate-fade-in bg-gradient-to-b from-[var(--surface-2)] to-transparent">
          <div className="flex items-center justify-between bg-[var(--surface-1)] p-3 rounded-lg border border-[var(--border-subtle)] text-xs text-[var(--text-muted)]">
            <span className="font-semibold text-[var(--text-primary)]">
              {currentSection}
            </span>
            <div className="flex items-center gap-3">
              <span>
                Type:{" "}
                <strong className="text-[var(--text-primary)]">
                  {currentType.replace(/_/g, " ")}
                </strong>
              </span>
              <span>•</span>
              <span>
                Fixed Marks:{" "}
                <strong className="text-[var(--text-primary)]">
                  {currentMarks}
                </strong>
              </span>
            </div>
          </div>

          <div className="space-y-4">
            {/* The Question Prompt */}
            <div className="space-y-1.5">
              <Label>
                Question Prompt <span className="text-red-400">*</span>
              </Label>
              <Textarea
                placeholder="Type your question here..."
                value={question.text}
                onChange={(e) => updateField("text", e.target.value)}
                className="text-base min-h-[100px] bg-[var(--surface-1)]"
              />
            </div>

            {/* Render dynamically branchable Options component */}
            <QuestionOptions
              type={currentType}
              options={question.options || []}
              onChange={(newOptions) => updateField("options", newOptions)}
            />
          </div>

          <hr className="border-[var(--border-subtle)]" />

          {/* Advanced / Optional settings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="space-y-1.5">
              <Label>Image URL (Optional)</Label>
              <Input
                placeholder="https://example.com/math-diagram.png"
                value={question.imageUrl || ""}
                onChange={(e) => updateField("imageUrl", e.target.value)}
              />
            </div>

            {(currentType === "SHORT_ANSWER" || currentType === "ESSAY") && (
              <div className="space-y-1.5">
                <Label>Maximum Word Limit</Label>
                <Input
                  type="number"
                  placeholder="e.g. 250"
                  value={question.wordLimit || ""}
                  onChange={(e) =>
                    updateField(
                      "wordLimit",
                      parseInt(e.target.value) || undefined
                    )
                  }
                />
              </div>
            )}

            <div className="space-y-1.5 md:col-span-2">
              <Label>Explanation / Solution (Optional)</Label>
              <Textarea
                placeholder="Shown to students after grading to explain the correct answer."
                value={question.explanation || ""}
                onChange={(e) => updateField("explanation", e.target.value)}
                className="min-h-16"
              />
            </div>
          </div>
        </div>
      )}
    </GlassCard>
  );
}
