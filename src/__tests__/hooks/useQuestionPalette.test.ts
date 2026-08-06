import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAttemptStore } from '@/stores/useAttemptStore';
import { useQuestionPalette } from '@/hooks/useQuestionPalette';

describe('useQuestionPalette', () => {
  beforeEach(() => {
    useAttemptStore.getState().clearAttempt();
    useAttemptStore.getState().setAllState({
      answers: {
        'q-1': {
          id: 'ans-1',
          questionId: 'q-1',
          questionType: 'MULTIPLE_CHOICE',
          status: 'NOT_VISITED',
        },
        'q-2': {
          id: 'ans-2',
          questionId: 'q-2',
          questionType: 'ESSAY',
          status: 'VISITED_NOT_ANSWERED',
        },
        'q-3': {
          id: 'ans-3',
          questionId: 'q-3',
          questionType: 'MULTIPLE_CHOICE',
          status: 'ANSWERED',
          selectedOptions: [{ optionId: 'opt-1' }],
        },
      },
    });
  });

  it('setActiveQuestion transitions NOT_VISITED to VISITED_NOT_ANSWERED', () => {
    const { result } = renderHook(() => useQuestionPalette());

    act(() => {
      result.current.setActiveQuestion('q-1');
    });

    const store = useAttemptStore.getState();
    expect(store.activeQuestionId).toBe('q-1');
    expect(store.answers['q-1'].status).toBe('VISITED_NOT_ANSWERED');
  });

  it('setActiveQuestion does not change status of already ANSWERED question', () => {
    const { result } = renderHook(() => useQuestionPalette());

    act(() => {
      result.current.setActiveQuestion('q-3');
    });

    const store = useAttemptStore.getState();
    expect(store.activeQuestionId).toBe('q-3');
    expect(store.answers['q-3'].status).toBe('ANSWERED');
  });

  it('updateAnswer updates selectedOptions and sets status to ANSWERED', () => {
    const { result } = renderHook(() => useQuestionPalette());

    act(() => {
      result.current.updateAnswer('q-1', undefined, [{ optionId: 'opt-2' }]);
    });

    const store = useAttemptStore.getState();
    expect(store.answers['q-1'].selectedOptions).toEqual([{ optionId: 'opt-2' }]);
    expect(store.answers['q-1'].status).toBe('ANSWERED');
  });

  it('updateAnswer with empty answer transitions back to VISITED_NOT_ANSWERED', () => {
    const { result } = renderHook(() => useQuestionPalette());

    act(() => {
      result.current.updateAnswer('q-3', '', []);
    });

    const store = useAttemptStore.getState();
    expect(store.answers['q-3'].status).toBe('VISITED_NOT_ANSWERED');
  });

  it('markQuestionForReview marks question status as MARKED_FOR_REVIEW', () => {
    const { result } = renderHook(() => useQuestionPalette());

    act(() => {
      result.current.markQuestionForReview('q-1');
    });

    const store = useAttemptStore.getState();
    expect(store.answers['q-1'].status).toBe('MARKED_FOR_REVIEW');
  });

  it('unmarkQuestionForReview restores correct status based on whether answer exists', () => {
    const { result } = renderHook(() => useQuestionPalette());

    // Mark q-3 (which has answer)
    act(() => {
      result.current.markQuestionForReview('q-3');
    });
    expect(useAttemptStore.getState().answers['q-3'].status).toBe('MARKED_FOR_REVIEW');

    // Unmark q-3 -> should become ANSWERED
    act(() => {
      result.current.unmarkQuestionForReview('q-3');
    });
    expect(useAttemptStore.getState().answers['q-3'].status).toBe('ANSWERED');

    // Mark q-2 (which has no answer)
    act(() => {
      result.current.markQuestionForReview('q-2');
    });
    expect(useAttemptStore.getState().answers['q-2'].status).toBe('MARKED_FOR_REVIEW');

    // Unmark q-2 -> should become VISITED_NOT_ANSWERED
    act(() => {
      result.current.unmarkQuestionForReview('q-2');
    });
    expect(useAttemptStore.getState().answers['q-2'].status).toBe('VISITED_NOT_ANSWERED');
  });
});
