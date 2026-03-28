import React from 'react';
import ExamInfoStep from './ExamInfoStep';
import QuestionsStep from './QuestionsStep';
import OverviewStep from './OverviewStep';

interface StepsPageProps {
  step: number;
}

const StepsPage: React.FC<StepsPageProps> = ({ step }) => {
  let content = null;
  if (step === 1) content = <ExamInfoStep />;
  else if (step === 2) content = <QuestionsStep />;
  else if (step === 3) content = <OverviewStep />;

  return (
    <div className="exam-steps-page">
      {content}
    </div>
  );
};

export default StepsPage;
