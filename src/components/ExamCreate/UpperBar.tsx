import React from 'react';

interface UpperBarProps {
  step: number;
}

const steps = [1, 2, 3];

const UpperBar: React.FC<UpperBarProps> = ({ step }) => {
  return (
    <div className="exam-upperbar" style={{ display: 'flex', justifyContent: 'center', margin: '24px 0' }}>
      {steps.map((num) => (
        <div
          key={num}
          style={{
            width: 40,
            height: 40,
            borderRadius: '50%',
            background: num === step ? '#0070f3' : '#e0e0e0',
            color: num === step ? '#fff' : '#333',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 'bold',
            fontSize: 20,
            margin: '0 12px',
            transition: 'background 0.2s, color 0.2s',
            boxShadow: num === step ? '0 0 8px #0070f3' : 'none',
            border: num === step ? '2px solid #0070f3' : '2px solid #e0e0e0',
          }}
        >
          {num}
        </div>
      ))}
    </div>
  );
};

export default UpperBar;
