import React from 'react';
import Image from 'next/image';
import { useAttemptEngine } from '@/hooks/useAttemptEngine';
import { Question } from '@/types/question';
import { GlassCard } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';

interface AttemptQuestionProps {
  question: Question;
  questionIndex?: number;
  totalQuestions?: number;
}

export const AttemptQuestion = ({ question, questionIndex, totalQuestions }: AttemptQuestionProps) => {
  const { answers, updateAnswer, markQuestionForReview, unmarkQuestionForReview } = useAttemptEngine();

  const answerState = answers[question.id];
  const isMarked = answerState?.status === 'MARKED_FOR_REVIEW';

  const handleOptionToggle = (optionId: string) => {
    let currentSelected = answerState?.selectedOptions?.map(o => o.optionId) || [];
    
    if (question.questionType === 'MULTIPLE_CHOICE' || question.questionType === 'TRUE_FALSE') {
      currentSelected = [optionId]; // Single selection
    } else if (question.questionType === 'MULTIPLE_SELECT') {
      if (currentSelected.includes(optionId)) {
        currentSelected = currentSelected.filter(id => id !== optionId);
      } else {
        currentSelected = [...currentSelected, optionId];
      }
    }
    
    updateAnswer(question.id, answerState?.textAnswer, currentSelected.map(id => ({ optionId: id })));
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    updateAnswer(question.id, e.target.value, answerState?.selectedOptions);
  };

  const clearResponse = () => {
    updateAnswer(question.id, "", []);
  };

  const toggleReviewMark = (checked: boolean | string) => {
      if (checked) {
          markQuestionForReview(question.id);
      } else {
          unmarkQuestionForReview(question.id);
      }
  };

  const selectedOptionsList = answerState?.selectedOptions?.map(o => o.optionId) || [];

  // Determine display question numbering
  const displayNum = questionIndex !== undefined ? questionIndex + 1 : (question.questionNumber || 1);

  return (
    <GlassCard padding="lg" className="min-h-[500px] flex flex-col">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4 mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2 flex-wrap">
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              Question {displayNum}
              {totalQuestions ? (
                <span className="text-sm font-normal text-[var(--text-muted)] ml-2">
                  of {totalQuestions}
                </span>
              ) : null}
            </h2>
          </div>
          
          <div className="flex items-center gap-2 flex-wrap">
            {question.section && (
              <span className="text-xs font-semibold text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-0.5 rounded-md">
                {question.section}
              </span>
            )}
            <span className="text-xs text-[var(--text-muted)] bg-[var(--surface-3)] px-2.5 py-0.5 rounded-md capitalize">
              {question.questionType === 'MULTIPLE_CHOICE'
                ? 'Single Choice (MCQ)'
                : question.questionType === 'MULTIPLE_SELECT'
                ? 'Multiple Select'
                : question.questionType === 'TRUE_FALSE'
                ? 'True / False'
                : question.questionType === 'SHORT_ANSWER'
                ? 'Short Answer'
                : question.questionType.replace(/_/g, " ")}
            </span>
            {question.questionType === 'MULTIPLE_SELECT' && (
              <span className="text-[11px] text-amber-300 bg-amber-500/10 border border-amber-500/20 px-2.5 py-0.5 rounded-md font-medium">
                Multiple options may be correct
              </span>
            )}
          </div>
        </div>
        
        <div className="bg-indigo-500/10 border border-indigo-500/20 px-3.5 py-1.5 rounded-lg self-start shrink-0">
          <span className="text-indigo-400 font-semibold text-sm">
            {question.marks} Mark{question.marks === 1 ? '' : 's'}
          </span>
        </div>
      </div>

      <div className="flex-1 space-y-8">
        <div className="text-base md:text-lg text-[var(--text-primary)] leading-relaxed whitespace-pre-wrap">
          {question.text}
        </div>

        {question.imageUrl && (
          <Image
            src={question.imageUrl}
            alt="Question figure"
            width={768}
            height={432}
            unoptimized
            className="max-w-md w-full h-auto rounded-lg border border-[var(--border-subtle)]"
          />
        )}

        <div className="space-y-3 mt-8">
          {(question.questionType === 'MULTIPLE_CHOICE' || question.questionType === 'MULTIPLE_SELECT' || question.questionType === 'TRUE_FALSE') && (
            <div className="space-y-3">
              {(question.options || []).map((option) => (
                <label 
                  key={option.id} 
                  className={`flex items-start gap-4 p-4 rounded-xl border-2 transition-all cursor-pointer hover:bg-[var(--surface-2)] ${
                    selectedOptionsList.includes(option.id) 
                      ? 'border-indigo-500 bg-indigo-500/5' 
                      : 'border-[var(--border-subtle)] bg-[var(--surface-1)]'
                  }`}
                >
                  <div className="pt-0.5">
                    <input 
                      type={question.questionType === 'MULTIPLE_SELECT' ? 'checkbox' : 'radio'}
                      name={`question-${question.id}`}
                      className="w-5 h-5 accent-indigo-500 cursor-pointer"
                      checked={selectedOptionsList.includes(option.id)}
                      onChange={() => handleOptionToggle(option.id)}
                    />
                  </div>
                  <span className="text-[var(--text-primary)]">{option.text}</span>
                </label>
              ))}
            </div>
          )}

          {(question.questionType === 'SHORT_ANSWER' || question.questionType === 'ESSAY') && (
            <div className="space-y-2">
                <textarea
                  className="w-full h-48 p-4 rounded-xl bg-[var(--surface-1)] border border-[var(--border-subtle)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none transition-all placeholder:text-[var(--text-dimmed)]"
                  placeholder="Type your answer here..."
                  value={answerState?.textAnswer || ''}
                  onChange={handleTextChange}
                />
                {question.wordLimit && (
                   <p className="text-xs text-[var(--text-muted)] text-right">
                       Word limit: {question.wordLimit} words
                   </p>
                )}
            </div>
          )}
        </div>
      </div>

      <div className="mt-8 pt-6 border-t border-[var(--border-subtle)] flex items-center justify-between">
        <label className="flex items-center gap-2 cursor-pointer group">
            <Checkbox 
                checked={isMarked} 
                onCheckedChange={toggleReviewMark} 
                className="data-[state=checked]:bg-purple-600 data-[state=checked]:border-purple-600"
            />
            <span className="text-sm text-[var(--text-muted)] group-hover:text-white transition-colors">Mark for review</span>
        </label>
        
        <Button variant="ghost" size="sm" onClick={clearResponse} className="text-[var(--text-dimmed)] hover:text-white">
          Clear Response
        </Button>
      </div>
    </GlassCard>
  );
};
