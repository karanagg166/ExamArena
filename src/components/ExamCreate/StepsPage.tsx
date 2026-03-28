import React from 'react';
import { useRouter } from 'next/navigation';
import ExamInfoStep from './ExamInfoStep';
import QuestionsStep from './QuestionsStep';
import OverviewStep from './OverviewStep';

import type { ExamInfo } from './ExamInfoStep';
import type { Question } from './QuestionsStep';
import router from 'next/dist/shared/lib/router/router';
import { api } from '@/lib/axios';

interface StepsPageProps {
  step: number;
  onStepChange?: (step: number) => void;
}

const StepsPage: React.FC<StepsPageProps> = ({ step, onStepChange }) => {

  const router = useRouter();

  const [examInfo, setExamInfo] = React.useState<ExamInfo>({
    name: '',
    description: '',
    date: '',
    duration: 0,
    maxMarks: 0,
    type: '',
  });
  const [questions, setQuestions] = React.useState<Question[]>([]);

  // Handler to move to next step
  const handleNextFromQuestions = () => {
    if (onStepChange) onStepChange(3);
  };


  // Submission state
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  // Handler for final submit
  const handleSubmitExam = async () => {
    setIsSubmitting(true);
    try {
      const response1 = await api.post("/api/v1/createExamInfo", examInfo);
      console.log('Exam Info Response:', response1.data);
      const response2 = await api.post("/api/v1/createExamQuestions", questions.map(q => ({ ...q, examId: response1.data.examId })));
      console.log('Exam Questions Response:', response2.data);
      alert('Exam created successfully!');
      router.push('/teacher/exams');
    } catch (err) {
      alert('Failed to create exam.');
    } finally {
      setIsSubmitting(false);
    }
  };

  let content = null;
  if (step === 1) {
    content = <ExamInfoStep value={examInfo} onChange={setExamInfo} onStepChange={onStepChange} />;
  } else if (step === 2) {
    content = (
      <QuestionsStep
        questions={questions}
        setQuestions={setQuestions}
        maxMarks={examInfo.maxMarks}
        onNext={handleNextFromQuestions}
      />
    );
  } else if (step === 3) {
    content = (
      <OverviewStep
        examInfo={examInfo}
        questions={questions}
        onSubmit={handleSubmitExam}
        isSubmitting={isSubmitting}
      />
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-50 dark:bg-black py-12 px-2">
      {content}
    </div>
  );
};

export default StepsPage;
