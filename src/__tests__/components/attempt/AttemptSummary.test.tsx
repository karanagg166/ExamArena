import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AttemptSummary } from '@/components/attempt/AttemptSummary';
import * as attemptEngine from '@/hooks/useAttemptEngine';
import type { Question, QuestionType } from '@/types';
import type { QuestionAttemptState } from '@/stores/useAttemptStore';

vi.mock('@/hooks/useAttemptEngine', () => ({
  useAttemptEngine: vi.fn(),
}));

const mockQuestions: Question[] = [
  {
    id: 'q1',
    examId: 'exm_1',
    text: 'Question 1',
    questionNumber: 1,
    marks: 4,
    questionType: 'MULTIPLE_CHOICE' as QuestionType,
    section: 'Section A',
    createdAt: '2026-01-01T00:00:00Z',
    updatedAt: '2026-01-01T00:00:00Z',
  },
  {
    id: 'q2',
    examId: 'exm_1',
    text: 'Question 2',
    questionNumber: 2,
    marks: 4,
    questionType: 'MULTIPLE_CHOICE' as QuestionType,
    section: 'Section A',
    createdAt: '2026-01-01T00:00:00Z',
    updatedAt: '2026-01-01T00:00:00Z',
  },
  {
    id: 'q3',
    examId: 'exm_1',
    text: 'Question 3',
    questionNumber: 3,
    marks: 4,
    questionType: 'MULTIPLE_CHOICE' as QuestionType,
    section: 'Section B',
    createdAt: '2026-01-01T00:00:00Z',
    updatedAt: '2026-01-01T00:00:00Z',
  },
];

describe('Component: AttemptSummary (C26)', () => {
  it('C26: renders question numbers and statistics footer', () => {
    const handleSetActive = vi.fn();
    const mockAnswers: Record<string, QuestionAttemptState> = {
      q1: { id: 'a1', questionId: 'q1', questionType: 'MULTIPLE_CHOICE', status: 'ANSWERED' },
      q2: { id: 'a2', questionId: 'q2', questionType: 'MULTIPLE_CHOICE', status: 'VISITED_NOT_ANSWERED' },
      q3: { id: 'a3', questionId: 'q3', questionType: 'MULTIPLE_CHOICE', status: 'MARKED_FOR_REVIEW' },
    };

    vi.mocked(attemptEngine.useAttemptEngine).mockReturnValue({
      answers: mockAnswers,
      activeQuestionId: 'q1',
      setActiveQuestion: handleSetActive,
      examId: 'exm_1',
      attemptId: 'att_1',
      status: 'IN_PROGRESS',
      startedAt: '2026-01-01T00:00:00Z',
      timeRemainingSeconds: 300,
      initializeAttempt: vi.fn(),
      updateAnswer: vi.fn(),
      markQuestionForReview: vi.fn(),
      unmarkQuestionForReview: vi.fn(),
      decrementTime: vi.fn(),
      submitAttemptLocal: vi.fn(),
      clearAttempt: vi.fn(),
    });

    render(<AttemptSummary questions={mockQuestions} />);

    expect(screen.getByText('Answered')).toBeInTheDocument();
    expect(screen.getByText('Not Answered')).toBeInTheDocument();
    expect(screen.getByText('Marked Review')).toBeInTheDocument();

    // Check Question 1 button in Section A
    const q1Btn = screen.getByRole('button', { name: '1' });
    expect(q1Btn).toBeInTheDocument();
    fireEvent.click(q1Btn);
    expect(handleSetActive).toHaveBeenCalledWith('q1');
  });

  it('switches section tabs correctly', () => {
    vi.mocked(attemptEngine.useAttemptEngine).mockReturnValue({
      answers: {},
      activeQuestionId: 'q1',
      setActiveQuestion: vi.fn(),
      examId: 'exm_1',
      attemptId: 'att_1',
      status: 'IN_PROGRESS',
      startedAt: '2026-01-01T00:00:00Z',
      timeRemainingSeconds: 300,
      initializeAttempt: vi.fn(),
      updateAnswer: vi.fn(),
      markQuestionForReview: vi.fn(),
      unmarkQuestionForReview: vi.fn(),
      decrementTime: vi.fn(),
      submitAttemptLocal: vi.fn(),
      clearAttempt: vi.fn(),
    });

    render(<AttemptSummary questions={mockQuestions} />);

    const secBTab = screen.getByRole('button', { name: 'Section B' });
    expect(secBTab).toBeInTheDocument();

    fireEvent.click(secBTab);
    // Question 3 belongs to Section B
    expect(screen.getByRole('button', { name: '3' })).toBeInTheDocument();
  });
});
