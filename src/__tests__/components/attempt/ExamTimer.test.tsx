import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ExamTimer } from '@/components/attempt/ExamTimer';
import * as attemptEngine from '@/hooks/useAttemptEngine';
import type { AttemptStatus } from '@/types';

vi.mock('@/hooks/useAttemptEngine', () => ({
  useAttemptEngine: vi.fn(),
}));

function mockEngineState(timeRemaining: number | null, status: AttemptStatus = 'IN_PROGRESS') {
  return {
    timeRemainingSeconds: timeRemaining,
    status,
    examId: 'exm_1',
    attemptId: 'att_1',
    answers: {},
    startedAt: '2026-01-01T00:00:00Z',
    activeQuestionId: null,
    initializeAttempt: vi.fn(),
    setActiveQuestion: vi.fn(),
    updateAnswer: vi.fn(),
    markQuestionForReview: vi.fn(),
    unmarkQuestionForReview: vi.fn(),
    decrementTime: vi.fn(),
    submitAttemptLocal: vi.fn(),
    clearAttempt: vi.fn(),
  };
}

describe('Component: ExamTimer (C20-C21)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('C20: renders formatted MM:SS time string for normal time', () => {
    vi.mocked(attemptEngine.useAttemptEngine).mockReturnValue(mockEngineState(600));

    render(<ExamTimer onTimeUp={vi.fn()} />);
    expect(screen.getByText('10:')).toBeInTheDocument();
    expect(screen.getByText('00')).toBeInTheDocument();
  });

  it('C21: applies warning styling when under 5 minutes (<300s)', () => {
    vi.mocked(attemptEngine.useAttemptEngine).mockReturnValue(mockEngineState(240));

    const { container } = render(<ExamTimer onTimeUp={vi.fn()} />);
    expect(container.firstChild).toHaveClass('text-amber-400');
  });

  it('applies critical pulse styling when under 1 minute (<60s)', () => {
    vi.mocked(attemptEngine.useAttemptEngine).mockReturnValue(mockEngineState(45));

    const { container } = render(<ExamTimer onTimeUp={vi.fn()} />);
    expect(container.firstChild).toHaveClass('text-red-400');
    expect(container.firstChild).toHaveClass('animate-pulse');
  });

  it('calls onTimeUp when time reaches 0', () => {
    const handleTimeUp = vi.fn();
    vi.mocked(attemptEngine.useAttemptEngine).mockReturnValue(mockEngineState(0));

    render(<ExamTimer onTimeUp={handleTimeUp} />);
    expect(handleTimeUp).toHaveBeenCalledTimes(1);
  });

  it('renders null if timeRemainingSeconds is null', () => {
    vi.mocked(attemptEngine.useAttemptEngine).mockReturnValue(mockEngineState(null, 'NOT_ATTEMPTED'));

    const { container } = render(<ExamTimer onTimeUp={vi.fn()} />);
    expect(container.firstChild).toBeNull();
  });
});
