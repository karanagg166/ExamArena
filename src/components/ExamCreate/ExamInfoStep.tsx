'use client';
import React from 'react'

export interface ExamInfo {
  name: string;
  description: string;
  date: string;
  duration: number;
  maxMarks: number;
  type: string;
}

const EXAM_TYPES = [
  { value: 'MIDTERM', label: 'Midterm' },
  { value: 'FINAL', label: 'Final' },
  { value: 'QUIZ', label: 'Quiz' },
  { value: 'ASSIGNMENT', label: 'Assignment' },
  { value: 'MOCK', label: 'Mock' },
];

interface ExamInfoStepProps {
  value: ExamInfo;
  onChange: (value: ExamInfo) => void;
  onStepChange?: (step: number) => void;
}

const ExamInfoStep: React.FC<ExamInfoStepProps> = ({ value, onChange, onStepChange }) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value: val } = e.target;
    onChange({ ...value, [name]: name === 'duration' || name === 'maxMarks' ? Number(val) : val });
  };

  return (
    <form className="max-w-2xl w-full bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl p-10 space-y-8 border border-zinc-200 dark:border-zinc-800">
      <h2 className="text-3xl font-extrabold mb-2 text-zinc-900 dark:text-zinc-50 tracking-tight text-center">Create New Exam</h2>
      <p className="text-center text-zinc-600 dark:text-zinc-400 mb-6">Fill in the details below to set up your exam.</p>
      <div className="space-y-6">
        <div>
          <label className="block text-base font-semibold text-zinc-800 dark:text-zinc-100 mb-2">Exam Name</label>
          <input
            type="text"
            name="name"
            value={value.name}
            onChange={handleChange}
            className="w-full border border-zinc-300 dark:border-zinc-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-400 text-base bg-zinc-50 dark:bg-zinc-800 dark:text-zinc-50"
            placeholder="Enter exam name"
            required
          />
        </div>
        <div>
          <label className="block text-base font-semibold text-zinc-800 dark:text-zinc-100 mb-2">Description</label>
          <textarea
            name="description"
            value={value.description}
            onChange={handleChange}
            className="w-full border border-zinc-300 dark:border-zinc-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-400 text-base bg-zinc-50 dark:bg-zinc-800 dark:text-zinc-50"
            placeholder="Short description of the exam"
            rows={3}
            required
          />
        </div>
        <div className="flex flex-col md:flex-row gap-6">
          <div className="flex-1">
            <label className="block text-base font-semibold text-zinc-800 dark:text-zinc-100 mb-2">Date & Time</label>
            <input
              type="datetime-local"
              name="date"
              value={value.date}
              onChange={handleChange}
              className="w-full border border-zinc-300 dark:border-zinc-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-400 text-base bg-zinc-50 dark:bg-zinc-800 dark:text-zinc-50"
              required
            />
          </div>
          <div className="flex-1">
            <label className="block text-base font-semibold text-zinc-800 dark:text-zinc-100 mb-2">Duration (minutes)</label>
            <input
              type="number"
              name="duration"
              value={value.duration}
              onChange={handleChange}
              min={1}
              className="w-full border border-zinc-300 dark:border-zinc-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-400 text-base bg-zinc-50 dark:bg-zinc-800 dark:text-zinc-50"
              placeholder="e.g. 60"
              required
            />
          </div>
        </div>
        <div className="flex flex-col md:flex-row gap-6">
          <div className="flex-1">
            <label className="block text-base font-semibold text-zinc-800 dark:text-zinc-100 mb-2">Maximum Marks</label>
            <input
              type="number"
              name="maxMarks"
              value={value.maxMarks}
              onChange={handleChange}
              min={1}
              className="w-full border border-zinc-300 dark:border-zinc-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-400 text-base bg-zinc-50 dark:bg-zinc-800 dark:text-zinc-50"
              placeholder="e.g. 100"
              required
            />
          </div>
          <div className="flex-1">
            <label className="block text-base font-semibold text-zinc-800 dark:text-zinc-100 mb-2">Exam Type</label>
            <select
              name="type"
              value={value.type}
              onChange={handleChange}
              className="w-full border border-zinc-300 dark:border-zinc-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-400 text-base bg-zinc-50 dark:bg-zinc-800 dark:text-zinc-50"
              required
            >
              <option value="" disabled>Select type</option>
              {EXAM_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>
      <div className="flex justify-end pt-6">
        <button
          type="button"
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-2 rounded-lg shadow transition-colors text-base"
          onClick={() => onStepChange && onStepChange(2)}
        >
          Next
        </button>
      </div>
    </form>
  );
};

export default ExamInfoStep;
