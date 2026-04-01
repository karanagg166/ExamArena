import React, { useState } from "react";
import { QuestionCard } from "./QuestionCard";
import { Button } from "@/components/ui/button";
import { PlusCircle, SearchX } from "lucide-react";
import type { QuestionUpsert } from "@/types";
import { EmptyState } from "@/components/ui/empty-state";

interface QuestionListProps {
  questions: QuestionUpsert[];
  onChange: (questions: QuestionUpsert[]) => void;
}

export function QuestionList({ questions, onChange }: QuestionListProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const addQuestion = () => {
    const newQuestion: QuestionUpsert = {
      text: "",
      marks: 1,
      questionNumber: questions.length + 1,
      questionType: "MULTIPLE_CHOICE",
      examId: "placeholder", // Removed before submission to server via types or backend defaults
      options: [
        { text: "", optionNumber: 1, isCorrect: false },
        { text: "", optionNumber: 2, isCorrect: false },
      ],
    };
    onChange([...questions, newQuestion]);
    setExpandedIndex(questions.length); // Auto-expand new question
  };

  const updateQuestion = (index: number, updated: QuestionUpsert) => {
    const newQuestions = [...questions];
    newQuestions[index] = updated;
    onChange(newQuestions);
  };

  const deleteQuestion = (index: number) => {
    const newQuestions = questions.filter((_, i) => i !== index);
    // Auto re-sequence question numbers
    newQuestions.forEach((q, i) => (q.questionNumber = i + 1));
    onChange(newQuestions);
    
    // Fix expanded index
    if (expandedIndex === index) setExpandedIndex(null);
    else if (expandedIndex !== null && expandedIndex > index) setExpandedIndex(expandedIndex - 1);
  };

  const toggleExpand = (index: number) => {
    setExpandedIndex(expandedIndex === index ? null : index);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">
            Exam Questions
          </h2>
          <p className="text-[var(--text-muted)] text-sm mt-1">
            Build your paper by adding multiple-choice, essay, or short-answer questions.
          </p>
        </div>
        {questions.length > 0 && (
          <Button onClick={addQuestion} size="sm" variant="secondary" className="hidden sm:flex">
            <PlusCircle className="mr-2 h-4 w-4" /> Add Question
          </Button>
        )}
      </div>

      {questions.length === 0 ? (
        <EmptyState
          icon={SearchX}
          title="No Questions Added"
          description="Your exam is currently empty. Start by adding your first question."
          className="border border-dashed border-[var(--border-default)] rounded-2xl bg-[var(--surface-1)]"
          action={
            <Button onClick={addQuestion} variant="primary">
              <PlusCircle className="mr-2 h-4 w-4" /> Add First Question
            </Button>
          }
        />
      ) : (
        <div className="space-y-4">
          {questions.map((q, i) => (
            <QuestionCard
              key={i} // in a real app, assigning an internal stable ID per draft item is safer, but index is okay for straightforward lists
              index={i}
              question={q}
              isExpanded={expandedIndex === i}
              onToggleExpand={() => toggleExpand(i)}
              onChange={(updated) => updateQuestion(i, updated)}
              onDelete={() => deleteQuestion(i)}
            />
          ))}

          <Button 
            onClick={addQuestion} 
            variant="outline" 
            className="w-full mt-4 border-dashed border-[var(--border-strong)] text-[var(--accent)] hover:text-[var(--accent-hover)]"
          >
            <PlusCircle className="mr-2 h-4 w-4" /> Add Another Question
          </Button>
        </div>
      )}
    </div>
  );
}
