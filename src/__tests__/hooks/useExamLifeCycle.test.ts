import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAttemptStore } from '@/stores/useAttemptStore';
import { useExamLifeCycle } from '@/hooks/useExamLifeCycle';

describe('useExamLifeCycle', () => {
  beforeEach(() => {
    useAttemptStore.getState().clearAttempt();
  });

  it('initializeAttempt sets up initial exam attempt state', () => {
    const { result } = renderHook(() => useExamLifeCycle());

    const initialAnswers = [
      {
        id: 'ans-1',
        questionId: 'q-1',
        questionType: 'MULTIPLE_CHOICE' as const,
      },
      {
        id: 'ans-2',
        questionId: 'q-2',
        questionType: 'SHORT_ANSWER' as const,
        textAnswer: 'Pre-filled answer',
      },
    ];

    act(() => {
      result.current.initializeAttempt('exam-1', 'attempt-1', initialAnswers, '2026-08-06T10:00:00Z', 3600);
    });

    const store = useAttemptStore.getState();
    expect(store.examId).toBe('exam-1');
    expect(store.attemptId).toBe('attempt-1');
    expect(store.status).toBe('IN_PROGRESS');
    expect(store.timeRemainingSeconds).toBe(3600);
    expect(store.activeQuestionId).toBe('q-1');

    // First question becomes VISITED_NOT_ANSWERED
    expect(store.answers['q-1'].status).toBe('VISITED_NOT_ANSWERED');
    // Pre-filled question becomes ANSWERED
    expect(store.answers['q-2'].status).toBe('ANSWERED');
  });

  it('initializeAttempt ignores re-initialization if attemptId matches existing non-empty attempt', () => {
    const { result } = renderHook(() => useExamLifeCycle());

    const initialAnswers = [
      {
        id: 'ans-1',
        questionId: 'q-1',
        questionType: 'MULTIPLE_CHOICE' as const,
      },
    ];

    act(() => {
      result.current.initializeAttempt('exam-1', 'attempt-1', initialAnswers, '2026-08-06T10:00:00Z', 3600);
    });

    // Modify active question
    act(() => {
      useAttemptStore.getState().setAllState({ activeQuestionId: 'custom-q' });
    });

    // Attempt to re-initialize with same attemptId
    act(() => {
      result.current.initializeAttempt('exam-1', 'attempt-1', initialAnswers, '2026-08-06T10:00:00Z', 3600);
    });

    // Active question should remain custom-q (not reset)
    expect(useAttemptStore.getState().activeQuestionId).toBe('custom-q');
  });

  it('submitAttemptLocal updates status to SUBMITTED', () => {
    const { result } = renderHook(() => useExamLifeCycle());

    act(() => {
      useAttemptStore.getState().setAllState({ status: 'IN_PROGRESS' });
    });

    act(() => {
      result.current.submitAttemptLocal();
    });

    expect(useAttemptStore.getState().status).toBe('SUBMITTED');
  });

  it('clearAttemptLocal resets the store', () => {
    const { result } = renderHook(() => useExamLifeCycle());

    act(() => {
      useAttemptStore.getState().setAllState({ examId: 'exam-1', status: 'IN_PROGRESS' });
    });

    act(() => {
      result.current.clearAttemptLocal();
    });

    expect(useAttemptStore.getState().examId).toBeNull();
    expect(useAttemptStore.getState().status).toBe('NOT_ATTEMPTED');
  });
});
