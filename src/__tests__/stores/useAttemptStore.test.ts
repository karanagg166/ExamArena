import { describe, it, expect, beforeEach } from 'vitest';
import { useAttemptStore } from '@/stores/useAttemptStore';

describe('useAttemptStore', () => {
  beforeEach(() => {
    useAttemptStore.getState().clearAttempt();
  });

  it('starts with clean initial state', () => {
    const state = useAttemptStore.getState();
    expect(state.examId).toBeNull();
    expect(state.attemptId).toBeNull();
    expect(state.answers).toEqual({});
    expect(state.status).toBe('NOT_ATTEMPTED');
    expect(state.activeQuestionId).toBeNull();
    expect(state.timeRemainingSeconds).toBeNull();
  });

  it('setAllState merges new partial state', () => {
    useAttemptStore.getState().setAllState({
      examId: 'exam-123',
      attemptId: 'attempt-456',
      status: 'IN_PROGRESS',
      timeRemainingSeconds: 1800,
    });

    const state = useAttemptStore.getState();
    expect(state.examId).toBe('exam-123');
    expect(state.attemptId).toBe('attempt-456');
    expect(state.status).toBe('IN_PROGRESS');
    expect(state.timeRemainingSeconds).toBe(1800);
  });

  it('setAnswerState updates existing question answer state', () => {
    useAttemptStore.getState().setAllState({
      answers: {
        'q-1': {
          id: 'ans-1',
          questionId: 'q-1',
          questionType: 'MULTIPLE_CHOICE',
          status: 'NOT_VISITED',
        },
      },
    });

    useAttemptStore.getState().setAnswerState('q-1', {
      status: 'ANSWERED',
      selectedOptions: [{ optionId: 'opt-a' }],
    });

    const answers = useAttemptStore.getState().answers;
    expect(answers['q-1'].status).toBe('ANSWERED');
    expect(answers['q-1'].selectedOptions).toEqual([{ optionId: 'opt-a' }]);
  });

  it('setAnswerState does not throw for non-existent question', () => {
    expect(() => {
      useAttemptStore.getState().setAnswerState('non-existent', { status: 'ANSWERED' });
    }).not.toThrow();
  });

  it('clearAttempt resets store back to initial', () => {
    useAttemptStore.getState().setAllState({
      examId: 'e-1',
      attemptId: 'a-1',
      status: 'SUBMITTED',
      answers: {
        'q-1': {
          id: 'ans-1',
          questionId: 'q-1',
          questionType: 'ESSAY',
          status: 'ANSWERED',
        },
      },
    });

    useAttemptStore.getState().clearAttempt();

    const state = useAttemptStore.getState();
    expect(state.examId).toBeNull();
    expect(state.attemptId).toBeNull();
    expect(state.answers).toEqual({});
    expect(state.status).toBe('NOT_ATTEMPTED');
  });
});
