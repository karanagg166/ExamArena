"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { PlusCircle, Trash2, CheckCircle2, HelpCircle } from "lucide-react";
import type { QuestionUpsert, QuestionType, QuestionOptionCreate } from "@/types";

interface QuestionFormProps {
  initialQuestion?: Partial<QuestionUpsert>;
  defaultSection?: string;
  onSave: (question: QuestionUpsert) => void;
  onCancel?: () => void;
  isSubmitting?: boolean;
}

const QUESTION_TYPES: { label: string; value: QuestionType }[] = [
  { label: "Multiple Choice (Single)", value: "MULTIPLE_CHOICE" },
  { label: "Multiple Select (Multiple)", value: "MULTIPLE_SELECT" },
  { label: "True / False", value: "TRUE_FALSE" },
  { label: "Short Answer", value: "SHORT_ANSWER" },
  { label: "Essay / Descriptive", value: "ESSAY" },
];

export function QuestionForm({
  initialQuestion,
  defaultSection = "Section A",
  onSave,
  onCancel,
  isSubmitting = false,
}: QuestionFormProps) {
  const [text, setText] = useState(initialQuestion?.text || "");
  const [section, setSection] = useState(initialQuestion?.section || defaultSection);
  const [questionType, setQuestionType] = useState<QuestionType>(
    initialQuestion?.questionType || "MULTIPLE_CHOICE"
  );
  const [marks, setMarks] = useState<number>(initialQuestion?.marks ?? 1);
  const [hasNegativeMarks, setHasNegativeMarks] = useState<boolean>(
    Boolean(initialQuestion?.negativeMarks && initialQuestion.negativeMarks > 0)
  );
  const [negativeMarks, setNegativeMarks] = useState<number>(
    initialQuestion?.negativeMarks ?? 0.25
  );
  const [explanation, setExplanation] = useState(initialQuestion?.explanation || "");
  const [referenceAnswer, setReferenceAnswer] = useState(
    initialQuestion?.referenceAnswer || ""
  );
  const [wordLimit, setWordLimit] = useState<number | undefined>(
    initialQuestion?.wordLimit
  );

  const [options, setOptions] = useState<QuestionOptionCreate[]>(() => {
    if (initialQuestion?.options && initialQuestion.options.length > 0) {
      return initialQuestion.options.map((opt, i) => ({
        optionNumber: opt.optionNumber ?? i + 1,
        text: opt.text || "",
        isCorrect: Boolean(opt.isCorrect),
      }));
    }
    if (questionType === "TRUE_FALSE") {
      return [
        { optionNumber: 1, text: "True", isCorrect: true },
        { optionNumber: 2, text: "False", isCorrect: false },
      ];
    }
    return [
      { optionNumber: 1, text: "", isCorrect: true },
      { optionNumber: 2, text: "", isCorrect: false },
      { optionNumber: 3, text: "", isCorrect: false },
      { optionNumber: 4, text: "", isCorrect: false },
    ];
  });

  const [error, setError] = useState<string | null>(null);

  const handleTypeChange = (newType: QuestionType) => {
    setQuestionType(newType);
    if (newType === "TRUE_FALSE") {
      setOptions([
        { optionNumber: 1, text: "True", isCorrect: true },
        { optionNumber: 2, text: "False", isCorrect: false },
      ]);
    } else if (newType === "MULTIPLE_CHOICE" || newType === "MULTIPLE_SELECT") {
      if (options.length < 2) {
        setOptions([
          { optionNumber: 1, text: "", isCorrect: true },
          { optionNumber: 2, text: "", isCorrect: false },
        ]);
      }
    }
  };

  const handleOptionTextChange = (index: number, val: string) => {
    const next = [...options];
    next[index] = { ...next[index], text: val };
    setOptions(next);
  };

  const handleOptionCorrectToggle = (index: number) => {
    if (questionType === "MULTIPLE_CHOICE" || questionType === "TRUE_FALSE") {
      setOptions(
        options.map((opt, i) => ({
          ...opt,
          isCorrect: i === index,
        }))
      );
    } else if (questionType === "MULTIPLE_SELECT") {
      const next = [...options];
      next[index] = { ...next[index], isCorrect: !next[index].isCorrect };
      setOptions(next);
    }
  };

  const addOption = () => {
    setOptions([
      ...options,
      {
        optionNumber: options.length + 1,
        text: "",
        isCorrect: false,
      },
    ]);
  };

  const removeOption = (index: number) => {
    if (options.length <= 2) {
      setError("At least two options are required for objective questions.");
      return;
    }
    const filtered = options
      .filter((_, i) => i !== index)
      .map((opt, i) => ({ ...opt, optionNumber: i + 1 }));
    setOptions(filtered);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!text.trim()) {
      setError("Question text is required.");
      return;
    }

    if (marks <= 0) {
      setError("Marks must be greater than 0.");
      return;
    }

    const isObjective =
      questionType === "MULTIPLE_CHOICE" ||
      questionType === "MULTIPLE_SELECT" ||
      questionType === "TRUE_FALSE";

    if (isObjective) {
      if (options.some((o) => !o.text.trim())) {
        setError("All options must contain text.");
        return;
      }
      if (!options.some((o) => o.isCorrect)) {
        setError("At least one option must be marked as correct.");
        return;
      }
    }

    const payload: QuestionUpsert = {
      ...(initialQuestion?.id ? { id: initialQuestion.id } : {}),
      text: text.trim(),
      section: section.trim() || defaultSection,
      questionType,
      marks: Number(marks),
      negativeMarks: hasNegativeMarks ? Number(negativeMarks) : 0,
      explanation: explanation.trim() || undefined,
      referenceAnswer: referenceAnswer.trim() || undefined,
      wordLimit: wordLimit ? Number(wordLimit) : undefined,
      questionNumber: initialQuestion?.questionNumber ?? 1,
      options: isObjective ? options : [],
    };

    onSave(payload);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label className="text-xs font-semibold text-zinc-400">Section</Label>
          <Input
            value={section}
            onChange={(e) => setSection(e.target.value)}
            placeholder="e.g. Section A"
            className="mt-1"
          />
        </div>

        <div>
          <Label className="text-xs font-semibold text-zinc-400">Question Type</Label>
          <Select
            value={questionType}
            onChange={(e) => handleTypeChange(e.target.value as QuestionType)}
            className="mt-1"
          >
            {QUESTION_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <div>
        <Label className="text-xs font-semibold text-zinc-400">Question Prompt</Label>
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type the full question prompt or instructions here..."
          rows={4}
          className="mt-1"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <Label className="text-xs font-semibold text-zinc-400">Marks (Positive)</Label>
          <Input
            type="number"
            min={1}
            step={0.5}
            value={marks}
            onChange={(e) => setMarks(parseFloat(e.target.value) || 1)}
            className="mt-1"
          />
        </div>

        <div>
          <Label className="text-xs font-semibold text-zinc-400">Negative Marking</Label>
          <div className="flex items-center gap-3 mt-2">
            <input
              type="checkbox"
              id="neg-marks-toggle"
              checked={hasNegativeMarks}
              onChange={(e) => setHasNegativeMarks(e.target.checked)}
              className="h-4 w-4 rounded border-zinc-700 bg-zinc-900 text-indigo-600 focus:ring-indigo-500"
            />
            <label htmlFor="neg-marks-toggle" className="text-xs text-zinc-300 cursor-pointer">
              Apply penalty for wrong answer
            </label>
          </div>
        </div>

        {hasNegativeMarks && (
          <div>
            <Label className="text-xs font-semibold text-zinc-400">Penalty (Deduction)</Label>
            <Input
              type="number"
              min={0}
              step={0.25}
              value={negativeMarks}
              onChange={(e) => setNegativeMarks(parseFloat(e.target.value) || 0)}
              className="mt-1"
            />
          </div>
        )}
      </div>

      {(questionType === "MULTIPLE_CHOICE" ||
        questionType === "MULTIPLE_SELECT" ||
        questionType === "TRUE_FALSE") && (
        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between">
            <Label className="text-xs font-semibold text-zinc-400">
              Answer Options (Select correct answer{questionType === "MULTIPLE_SELECT" ? "s" : ""})
            </Label>
            {questionType !== "TRUE_FALSE" && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addOption}
                className="text-xs"
              >
                <PlusCircle className="mr-1.5 h-3.5 w-3.5" />
                Add Option
              </Button>
            )}
          </div>

          <div className="space-y-2">
            {options.map((opt, i) => (
              <div
                key={i}
                className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${
                  opt.isCorrect
                    ? "border-emerald-500/40 bg-emerald-950/20"
                    : "border-zinc-800 bg-zinc-900/40"
                }`}
              >
                <button
                  type="button"
                  onClick={() => handleOptionCorrectToggle(i)}
                  className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border text-xs font-bold transition-colors ${
                    opt.isCorrect
                      ? "border-emerald-500 bg-emerald-500 text-white"
                      : "border-zinc-700 bg-zinc-800 text-zinc-400 hover:border-zinc-500"
                  }`}
                  title="Toggle as correct answer"
                >
                  {opt.isCorrect ? <CheckCircle2 className="h-4 w-4" /> : String.fromCharCode(65 + i)}
                </button>

                <Input
                  value={opt.text}
                  onChange={(e) => handleOptionTextChange(i, e.target.value)}
                  placeholder={`Option ${String.fromCharCode(65 + i)} text`}
                  className="flex-1 bg-transparent border-none focus-visible:ring-0 text-sm"
                  disabled={questionType === "TRUE_FALSE"}
                />

                {questionType !== "TRUE_FALSE" && options.length > 2 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => removeOption(i)}
                    className="h-8 w-8 p-0 text-zinc-500 hover:text-red-400"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {(questionType === "SHORT_ANSWER" || questionType === "ESSAY") && (
        <div className="space-y-4 pt-2">
          <div>
            <Label className="text-xs font-semibold text-zinc-400">
              Reference / Model Answer (for automated & AI grading)
            </Label>
            <Textarea
              value={referenceAnswer}
              onChange={(e) => setReferenceAnswer(e.target.value)}
              placeholder="Provide ideal key points, terms, or sample solution..."
              rows={3}
              className="mt-1"
            />
          </div>

          <div>
            <Label className="text-xs font-semibold text-zinc-400">Word Limit (Optional)</Label>
            <Input
              type="number"
              min={10}
              step={10}
              value={wordLimit ?? ""}
              onChange={(e) =>
                setWordLimit(e.target.value ? parseInt(e.target.value, 10) : undefined)
              }
              placeholder="e.g. 250"
              className="mt-1"
            />
          </div>
        </div>
      )}

      <div>
        <Label className="text-xs font-semibold text-zinc-400 flex items-center gap-1.5">
          <HelpCircle className="h-3.5 w-3.5" />
          Explanation / Solution Walkthrough (Displayed after results are released)
        </Label>
        <Textarea
          value={explanation}
          onChange={(e) => setExplanation(e.target.value)}
          placeholder="Explain why the answer is correct to assist student revision..."
          rows={2}
          className="mt-1"
        />
      </div>

      <div className="flex items-center justify-end gap-3 pt-4 border-t border-zinc-800">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </Button>
        )}
        <Button
          type="submit"
          disabled={isSubmitting}
          className="bg-indigo-600 hover:bg-indigo-700 text-white"
        >
          {isSubmitting ? "Saving Question..." : "Save Question"}
        </Button>
      </div>
    </form>
  );
}

export default QuestionForm;
