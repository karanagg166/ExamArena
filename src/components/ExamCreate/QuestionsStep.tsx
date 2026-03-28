'use client';
import React from 'react'

export interface Question {
  text: string;
  options: string[];
  correctAnswer: string;
  marks: number;
}

interface QuestionsStepProps {
  questions: Question[];
  setQuestions: (questions: Question[]) => void;
  maxMarks: number;
  onNext: () => void;
}

const QuestionsStep: React.FC<QuestionsStepProps> = ({ questions, setQuestions, maxMarks, onNext }) => {
  const [current, setCurrent] = React.useState<Question>({
    text: '',
    options: ['', '', '', ''],
    correctAnswer: '',
    marks: 0,
  });
  const [error, setError] = React.useState('');

  const totalMarks = questions.reduce((sum, q) => sum + q.marks, 0);

  const handleOptionChange = (idx: number, value: string) => {
    const newOptions = [...current.options];
    newOptions[idx] = value;
    setCurrent({ ...current, options: newOptions });
  };

  const handleAddQuestion = () => {
    if (!current.text.trim() || current.options.some(opt => !opt.trim()) || !current.correctAnswer.trim() || !current.marks) {
      setError('Please fill all fields for the question.');
      return;
    }
    if (!current.options.includes(current.correctAnswer)) {
      setError('Correct answer must match one of the options.');
      return;
    }
    if (totalMarks + current.marks > maxMarks) {
      setError('Total marks cannot exceed maximum marks.');
      return;
    }
    setQuestions([...questions, current]);
    setCurrent({ text: '', options: ['', '', '', ''], correctAnswer: '', marks: 0 });
    setError('');
  };

  return (
    <div className="max-w-2xl w-full bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl p-10 space-y-8 border border-zinc-200 dark:border-zinc-800">
      <h2 className="text-3xl font-extrabold mb-2 text-zinc-900 dark:text-zinc-50 tracking-tight text-center">Add Questions</h2>
      <p className="text-center text-zinc-600 dark:text-zinc-400 mb-6">Total Marks: <span className="font-semibold text-blue-700 dark:text-blue-400">{totalMarks}</span> / {maxMarks}</p>
      {error && <div className="text-red-600 text-center mb-2">{error}</div>}
      <div className="space-y-4">
        <div>
          <label className="block text-base font-semibold text-zinc-800 dark:text-zinc-100 mb-2">Marks for this Question</label>
          <input
            type="number"
            min={1}
            max={maxMarks - totalMarks}
            value={current.marks || ''}
            onChange={e => setCurrent({ ...current, marks: Number(e.target.value) })}
            className="w-full border border-zinc-300 dark:border-zinc-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-400 text-base bg-zinc-50 dark:bg-zinc-800 dark:text-zinc-50"
            placeholder="e.g. 5"
          />
        </div>
        <div>
          <label className="block text-base font-semibold text-zinc-800 dark:text-zinc-100 mb-2">Question</label>
          <input
            type="text"
            value={current.text}
            onChange={e => setCurrent({ ...current, text: e.target.value })}
            className="w-full border border-zinc-300 dark:border-zinc-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-400 text-base bg-zinc-50 dark:bg-zinc-800 dark:text-zinc-50"
            placeholder="Enter question text"
          />
        </div>
        <div>
          <label className="block text-base font-semibold text-zinc-800 dark:text-zinc-100 mb-2">Options</label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {current.options.map((opt, idx) => (
              <input
                key={idx}
                type="text"
                value={opt}
                onChange={e => handleOptionChange(idx, e.target.value)}
                className="border border-zinc-300 dark:border-zinc-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-400 text-base bg-zinc-50 dark:bg-zinc-800 dark:text-zinc-50"
                placeholder={`Option ${idx + 1}`}
              />
            ))}
          </div>
        </div>
        <div>
          <label className="block text-base font-semibold text-zinc-800 dark:text-zinc-100 mb-2">Correct Option</label>
          <input
            type="text"
            value={current.correctAnswer}
            onChange={e => setCurrent({ ...current, correctAnswer: e.target.value })}
            className="w-full border border-zinc-300 dark:border-zinc-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-400 text-base bg-zinc-50 dark:bg-zinc-800 dark:text-zinc-50"
            placeholder="Enter correct option (must match one above)"
          />
        </div>
        <div className="flex justify-end pt-4">
          <button
            type="button"
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-2 rounded-lg shadow transition-colors text-base"
            onClick={handleAddQuestion}
            disabled={totalMarks >= maxMarks}
          >
            Add Question
          </button>
        </div>
      </div>
      <div className="mt-8">
        <h3 className="text-lg font-bold mb-2 text-zinc-800 dark:text-zinc-100">Questions Added</h3>
        <ul className="space-y-2">
          {questions.map((q, idx) => (
            <li key={idx} className="bg-zinc-100 dark:bg-zinc-800 rounded p-3 flex flex-col md:flex-row md:items-center md:justify-between">
              <span className="font-medium text-zinc-900 dark:text-zinc-50">Q{idx + 1}: {q.text}</span>
              <span className="text-sm text-zinc-500 dark:text-zinc-300">Marks: {q.marks}</span>
            </li>
          ))}
        </ul>
      </div>
      <div className="flex justify-end pt-6">
        <button
          type="button"
          className={`bg-green-600 hover:bg-green-700 text-white font-semibold px-8 py-2 rounded-lg shadow transition-colors text-base ${totalMarks === maxMarks ? '' : 'opacity-50 cursor-not-allowed'}`}
          onClick={onNext}
          disabled={totalMarks !== maxMarks}
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default QuestionsStep;
