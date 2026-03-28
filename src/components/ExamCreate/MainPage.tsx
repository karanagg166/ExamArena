import React from 'react';
import UpperBar from './UpperBar';
import StepsPage from './StepsPage';

const MainPage = () => {

    const [currentStep, setCurrentStep] = React.useState(1);

  return (
    <div className="exam-create-mainpage">
      <UpperBar step={currentStep} onStepChange={setCurrentStep} />
      <div className="exam-create-content">
        <StepsPage step={currentStep} />
      </div>
    </div>
  );
};

export default MainPage;
