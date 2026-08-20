import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ExamCard } from '@/components/exam/ExamCard';
import type { Exam, ExamType, Subject, QuestionType } from '@/types';

const mockExam: Exam = {
  id: 'exm_123',
  examCode: 'EXM-ABC123',
  name: 'Midterm Physics Assessment',
  description: 'Comprehensive test covering mechanics and thermodynamics',
  scheduledAt: '2026-09-15T10:00:00Z',
  duration: 90,
  maxMarks: 100,
  type: 'MIDTERM' as ExamType,
  subject: 'SCIENCE' as Subject,
  isPublished: true,
  isPublic: true,
  isResultsReleased: false,
  negativeMarking: true,
  negativeMarks: 1.0,
  teacherId: 'tch_1',
  questions: [
    {
      id: 'q1',
      examId: 'exm_123',
      text: 'Q1',
      questionNumber: 1,
      marks: 5,
      questionType: 'MULTIPLE_CHOICE' as QuestionType,
      section: 'Section A',
      createdAt: '2026-09-01T00:00:00Z',
      updatedAt: '2026-09-01T00:00:00Z',
    },
    {
      id: 'q2',
      examId: 'exm_123',
      text: 'Q2',
      questionNumber: 2,
      marks: 5,
      questionType: 'MULTIPLE_CHOICE' as QuestionType,
      section: 'Section A',
      createdAt: '2026-09-01T00:00:00Z',
      updatedAt: '2026-09-01T00:00:00Z',
    },
  ],
  createdAt: '2026-09-01T00:00:00Z',
  updatedAt: '2026-09-01T00:00:00Z',
};

describe('Component: ExamCard (C6-C8)', () => {
  it('C6: renders exam title and description', () => {
    render(<ExamCard exam={mockExam} />);
    expect(screen.getByText('Midterm Physics Assessment')).toBeInTheDocument();
    expect(screen.getByText(/Comprehensive test covering mechanics/i)).toBeInTheDocument();
  });

  it('C7: renders exam code, type badge, and published status badge', () => {
    render(<ExamCard exam={mockExam} />);
    expect(screen.getByText(/EXM-ABC123/)).toBeInTheDocument();
    expect(screen.getByText('MIDTERM')).toBeInTheDocument();
    expect(screen.getByText(/Published/i)).toBeInTheDocument();
  });

  it('C8: renders duration, questions count, and marks info', () => {
    render(<ExamCard exam={mockExam} />);
    expect(screen.getByText('90 mins')).toBeInTheDocument();
    expect(screen.getByText('2 Questions')).toBeInTheDocument();
    expect(screen.getByText('100 Marks')).toBeInTheDocument();
  });

  it('renders Draft badge when exam is not published', () => {
    const draftExam = { ...mockExam, isPublished: false };
    render(<ExamCard exam={draftExam} />);
    expect(screen.getByText(/Draft/i)).toBeInTheDocument();
  });

  it('renders scheduled date in IST', () => {
    render(<ExamCard exam={mockExam} />);
    // 2026-09-15T10:00:00Z -> 15 Sep 2026, 3:30 PM IST
    expect(screen.getByText(/15 Sep 2026.*IST/i)).toBeInTheDocument();
  });
});
