import React, { useState } from "react";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { ChevronDown, ChevronUp, Trash2, GripVertical } from "lucide-react";
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
}

const QUESTION_TYPES: { label: string; value: QuestionType }[] = [
  { label: "Multiple Choice", value: "MULTIPLE_CHOICE" },
  { label: "Multiple Select", value: "MULTIPLE_SELECT" },
  { label: "True / False", value: "TRUE_FALSE" },
  { label: "Short Answer", value: "SHORT_ANSWER" },
  { label: "Essay / Paragraph", value: "ESSAY" },
];

export function QuestionCard({
  question,
  index,
  isExpanded,
  onToggleExpand,
  onChange,
  onDelete,
}: QuestionCardProps) {
  // Simple update helper
  const updateField = (field: keyof QuestionUpsert, value: any) => {
    onChange({ ...question, [field]: value });
  };

  const handleTypeChange = (newType: QuestionType) => {
    // If switching to short answer/essay, we can clear options to clean payload.
    // If switching between multiple choice types, we might want to reset correct answers.
    let updatedOptions = question.options;
    if (newType === "TRUE_FALSE") {
      updatedOptions = []; // The options component will auto-populate true/false
    } else if (newType === "SHORT_ANSWER" || newType === "ESSAY") {
      updatedOptions = [];
    }

    onChange({
      ...question,
      questionType: newType,
      options: updatedOptions,
    });
  };

  return (
    <GlassCard padding="none" className="overflow-hidden transition-smooth border border-[var(--border-default)]">
      {/* ─── Compact Header (Always visible) ─── */}
      <div 
        className={cn(
          "flex items-center gap-3 p-4 cursor-pointer hover:bg-[var(--surface-2)] transition-colors",
          isExpanded ? "border-b border-[var(--border-subtle)] bg-[var(--surface-2)]" : ""
        )}
        onClick={onToggleExpand}
      >
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-[var(--surface-3)] text-sm font-semibold text-[var(--accent)] shrink-0">
          {index + 1}
        </div>
        
        <div className="flex-grow flex flex-col sm:flex-row gap-2 sm:items-center justify-between">
          <p className="text-sm font-medium text-[var(--text-primary)] line-clamp-1 truncate pe-4">
            {question.text || <span className="text-[var(--text-dimmed)] italic">Empty Question...</span>}
          </p>
          
          <div className="flex items-center gap-2 shrink-0">
            <Badge variant="neutral" className="text-[10px] hidden sm:inline-flex">
              {question.questionType.replace("_", " ")}
            </Badge>
            <Badge variant="default" className="text-[10px]">
              {question.marks} Marks
            </Badge>
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0 ml-2">
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onDelete(); }}
            className="p-1.5 text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
            title="Delete Question"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <div className="p-1.5 text-[var(--text-muted)]">
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </div>
      </div>

      {/* ─── Expanded Body Editor ─── */}
      {isExpanded && (
        <div className="p-5 md:p-6 space-y-6 animate-fade-in bg-gradient-to-b from-[var(--surface-2)] to-transparent">
          {/* Top Controls Row */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
            <div className="md:col-span-5 space-y-1.5">
              <Label>Question Type</Label>
              <Select 
                value={question.questionType}
                onChange={(e) => handleTypeChange(e.target.value as QuestionType)}
              >
                {QUESTION_TYPES.map(t => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </Select>
            </div>
            
            <div className="md:col-span-3 space-y-1.5">
              <Label>Marks</Label>
              <Input 
                type="number"
                min="0"
                value={question.marks || ""}
                onChange={(e) => updateField("marks", parseInt(e.target.value) || 0)}
              />
            </div>

            <div className="md:col-span-4 space-y-1.5">
              <Label>Section Topic (Optional)</Label>
              <Input 
                placeholder="e.g. Grammar"
                value={question.section || ""}
                onChange={(e) => updateField("section", e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-4">
            {/* The Question Prompt */}
            <div className="space-y-1.5">
              <Label>Question Prompt <span className="text-red-400">*</span></Label>
              <Textarea
                placeholder="Type your question here..."
                value={question.text}
                onChange={(e) => updateField("text", e.target.value)}
                className="text-base min-h-[100px] bg-[var(--surface-1)]"
              />
            </div>

            {/* Render dynamically branchable Options component */}
            <QuestionOptions 
              type={question.questionType}
              options={question.options || []}
              onChange={(newOptions) => updateField("options", newOptions)}
            />
          </div>

          <hr className="border-[var(--border-subtle)]" />

          {/* Advanced / Optional settings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="space-y-1.5">
              <Label>Image URL Wrapper</Label>
              <Input 
                placeholder="https://example.com/math-graph.png"
                value={question.imageUrl || ""}
                onChange={(e) => updateField("imageUrl", e.target.value)}
              />
            </div>

            {(question.questionType === "SHORT_ANSWER" || question.questionType === "ESSAY") && (
              <div className="space-y-1.5">
                <Label>Maximum Word Limit</Label>
                <Input 
                  type="number"
                  placeholder="e.g. 250"
                  value={question.wordLimit || ""}
                  onChange={(e) => updateField("wordLimit", parseInt(e.target.value) || undefined)}
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
