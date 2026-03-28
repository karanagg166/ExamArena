import React from 'react';

interface StepsPageProps {
  step: number;
}

const ExamInfoStep = () => (
  <div>
    <h2>Exam Info</h2>
    {/* Input fields for exam name, class, subject, etc. */}
    <p>Exam info form goes here.</p>
  </div>
);

const QuestionsStep = () => (
  <div>
    <h2>Questions</h2>
    {/* Form for adding questions and answers */}
    <p>Questions form goes here.</p>
  </div>
);

const OverviewStep = () => (
  <div>
    <h2>Overview</h2>
    {/* Overview of all entered data for confirmation */}
    <p>Overview of exam and questions goes here.</p>
  </div>
);

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
