import React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PlusCircle, Trash2, CheckCircle2, Circle } from "lucide-react";
import type { QuestionType } from "@/types";
import type { QuestionOption } from "@/types/question";

interface QuestionOptionsProps {
  type: QuestionType;
  options: (Partial<QuestionOption> & { text: string; isCorrect: boolean; optionNumber: number })[];
  onChange: (options: (Partial<QuestionOption> & { text: string; isCorrect: boolean; optionNumber: number })[]) => void;
}

export function QuestionOptions({ type, options, onChange }: QuestionOptionsProps) {
  if (type === "SHORT_ANSWER" || type === "ESSAY") {
    return null;
  }

  // Auto-initialize True/False
  React.useEffect(() => {
    if (type === "TRUE_FALSE" && options.length !== 2) {
      onChange([
        { text: "True", isCorrect: true, optionNumber: 1 },
        { text: "False", isCorrect: false, optionNumber: 2 },
      ]);
    }
  }, [type, options.length, onChange]);

  const addOption = () => {
    onChange([
      ...options,
      {
        text: "",
        isCorrect: false,
        optionNumber: options.length + 1,
      },
    ]);
  };

  const removeOption = (index: number) => {
    const newOptions = options.filter((_, i) => i !== index);
    // Re-index
    newOptions.forEach((opt, i) => {
      opt.optionNumber = i + 1;
    });
    onChange(newOptions);
  };

  const updateOptionText = (index: number, text: string) => {
    const newOptions = [...options];
    newOptions[index].text = text;
    onChange(newOptions);
  };

  const toggleCorrect = (index: number) => {
    const newOptions = [...options];

    if (type === "MULTIPLE_CHOICE" || type === "TRUE_FALSE") {
      // Only one correct option allowed
      newOptions.forEach((opt, i) => {
        opt.isCorrect = i === index;
      });
    } else {
      // Multiple selection allows toggling independently
      newOptions[index].isCorrect = !newOptions[index].isCorrect;
    }

    onChange(newOptions);
  };

  return (
    <div className="space-y-3 mt-4">
      <div className="flex justify-between items-center mb-2">
        <Label>Answer Options</Label>
        <span className="text-xs text-[var(--text-muted)]">
          {type === "MULTIPLE_CHOICE" || type === "TRUE_FALSE"
            ? "Select the correct answer"
            : "Select all correct answers"}
        </span>
      </div>

      <div className="space-y-3">
        {options.map((opt, index) => (
          <div
            key={index}
            className={`flex items-center gap-3 p-3 rounded-xl border transition-colors ${
              opt.isCorrect
                ? "bg-[var(--success-muted)] border-[var(--success)]/30 shadow-[0_0_10px_rgba(16,185,129,0.1)]"
                : "bg-[var(--surface-2)] border-[var(--border-subtle)]"
            }`}
          >
            {/* Correctness Toggle */}
            <button
              type="button"
              onClick={() => toggleCorrect(index)}
              className="flex-shrink-0 focus:outline-none"
              title="Mark as correct"
            >
              {opt.isCorrect ? (
                <CheckCircle2 className="w-6 h-6 text-[var(--success)]" />
              ) : (
                <Circle className="w-6 h-6 text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors" />
              )}
            </button>

            {/* Option Text Input */}
            <div className="flex-grow">
              {type === "TRUE_FALSE" ? (
                <span className="text-sm font-medium px-2 py-1 text-[var(--text-primary)]">
                  {opt.text}
                </span>
              ) : (
                <Input
                  placeholder={`Option ${index + 1}`}
                  value={opt.text}
                  onChange={(e) => updateOptionText(index, e.target.value)}
                  className="bg-transparent border-none shadow-none focus-visible:ring-0 px-2 h-8"
                />
              )}
            </div>

            {/* Remove Button (Hide for True/False) */}
            {type !== "TRUE_FALSE" && (
              <button
                type="button"
                onClick={() => removeOption(index)}
                className="flex-shrink-0 text-red-400/60 hover:text-red-400 hover:bg-red-400/10 p-1.5 rounded-lg transition-colors focus:outline-none"
                title="Remove Option"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        ))}
      </div>

      {type !== "TRUE_FALSE" && (
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={addOption}
          className="w-full mt-2 border-dashed border-[var(--border-strong)] text-[var(--accent)] hover:text-[var(--accent-hover)] hover:border-[var(--accent)]/50"
        >
          <PlusCircle className="h-4 w-4 mr-1.5" />
          Add Option
        </Button>
      )}
    </div>
  );
}
