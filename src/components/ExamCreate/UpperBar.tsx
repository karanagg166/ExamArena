'use client';

import React from 'react';


interface UpperBarProps {
  step: number;
  onStepChange?: (step: number) => void;
}

const steps = [1, 2, 3];


const UpperBar: React.FC<UpperBarProps> = ({ step, onStepChange }) => {
  return (
    <div className="exam-upperbar flex justify-center items-center my-6">
      {steps.map((num, idx) => (
        <React.Fragment key={num}>
          <button
            type="button"
            className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg transition-colors border-2 focus:outline-none ${
              num === step
                ? 'bg-blue-600 text-white border-blue-600 shadow-lg'
                : 'bg-gray-200 text-gray-700 border-gray-200 hover:bg-blue-100 hover:text-blue-700'
            }`}
            onClick={() => onStepChange && onStepChange(num)}
          >
            {num}
          </button>
          {idx < steps.length - 1 && (
            <div className="w-16 h-1 flex items-center mx-2">
              <div className="border-t-2 border-dashed border-gray-400 w-full"></div>
            </div>
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

export default UpperBar;
