'use client';
import React from 'react'


import type { ExamInfo } from './ExamInfoStep';
import type { Question } from './QuestionsStep';

interface OverviewStepProps {
  examInfo: ExamInfo;
  questions: Question[];
  onSubmit: () => void;
  isSubmitting: boolean;
}

const OverviewStep: React.FC<OverviewStepProps> = ({ examInfo, questions, onSubmit, isSubmitting }) => {
  return (
    <div className="max-w-2xl w-full bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl p-10 space-y-8 border border-zinc-200 dark:border-zinc-800">
      <h2 className="text-3xl font-extrabold mb-2 text-zinc-900 dark:text-zinc-50 tracking-tight text-center">Review & Submit Exam</h2>
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-bold text-zinc-800 dark:text-zinc-100 mb-2">Exam Details</h3>
          <ul className="text-zinc-700 dark:text-zinc-200 space-y-1">
            <li><span className="font-semibold">Name:</span> {examInfo.name}</li>
            <li><span className="font-semibold">Description:</span> {examInfo.description}</li>
            <li><span className="font-semibold">Date & Time:</span> {examInfo.date}</li>
            <li><span className="font-semibold">Duration:</span> {examInfo.duration} min</li>
            <li><span className="font-semibold">Max Marks:</span> {examInfo.maxMarks}</li>
            <li><span className="font-semibold">Type:</span> {examInfo.type}</li>
          </ul>
        </div>
        <div>
          <h3 className="text-lg font-bold text-zinc-800 dark:text-zinc-100 mb-2">Questions</h3>
          <ul className="space-y-4">
            {questions.map((q, idx) => (
              <li key={idx} className="bg-zinc-100 dark:bg-zinc-800 rounded p-3">
                <div className="font-medium text-zinc-900 dark:text-zinc-50">Q{idx + 1}: {q.text}</div>
                <div className="text-sm text-zinc-600 dark:text-zinc-300">Marks: {q.marks}</div>
                <div className="text-sm text-zinc-600 dark:text-zinc-300">Options: {q.options.join(', ')}</div>
                <div className="text-sm text-green-700 dark:text-green-400">Correct: {q.correctAnswer}</div>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="flex justify-end pt-6">
        <button
          type="button"
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-2 rounded-lg shadow transition-colors text-base disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={onSubmit}
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Submitting...' : 'Submit Exam'}
        </button>
      </div>
    </div>
  );
}

export default OverviewStep
