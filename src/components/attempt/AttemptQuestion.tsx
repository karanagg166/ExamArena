import React from 'react';
import { useAttemptEngine } from '@/hooks/useAttemptEngine';
import { Question } from '@/types/question';
import { GlassCard } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';

export const AttemptQuestion = ({ question }: { question: Question }) => {
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

  return (
    <GlassCard padding="lg" className="min-h-[500px] flex flex-col">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-xl font-bold text-white mb-2">Question {question.questionNumber}</h2>
          {question.section && (
            <span className="text-xs text-[var(--text-dimmed)] bg-[var(--surface-3)] px-2 py-1 rounded-md">
                Section: {question.section}
            </span>
          )}
        </div>
        <div className="bg-indigo-500/10 border border-indigo-500/20 px-3 py-1.5 rounded-lg">
          <span className="text-indigo-400 font-medium">{question.marks} Marks</span>
        </div>
      </div>

      <div className="flex-1 space-y-8">
        <div className="text-lg text-[var(--text-primary)] leading-relaxed whitespace-pre-wrap">
          {question.text}
        </div>

        {question.imageUrl && (
          <img src={question.imageUrl} alt="Question figure" className="max-w-md w-full rounded-lg border border-[var(--border-subtle)]" />
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
                  className="w-full h-48 p-4 rounded-xl bg-[var(--surface-1)] border border-[var(--border-subtle)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none transition-all"
                  placeholder="Type your answer here..."
                  value={answerState?.textAnswer || ''}
                  onChange={handleTextChange}
                />
                {question.wordLimit && (
                   <p className="text-xs text-[var(--text-muted)] text-right">
                       Word limit: {question.wordLimit}
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
                className="data-[state=checked]:bg-blue-500 data-[state=checked]:border-blue-500"
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
