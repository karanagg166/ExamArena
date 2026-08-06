import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAttemptStore } from '@/stores/useAttemptStore';
import { useExamTimer } from '@/hooks/useExamTimer';

describe('useExamTimer', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useAttemptStore.getState().clearAttempt();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('decrements timeRemainingSeconds every second when status is IN_PROGRESS', () => {
    useAttemptStore.getState().setAllState({
      status: 'IN_PROGRESS',
      timeRemainingSeconds: 100,
    });

    renderHook(() => useExamTimer());

    expect(useAttemptStore.getState().timeRemainingSeconds).toBe(100);

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(useAttemptStore.getState().timeRemainingSeconds).toBe(99);

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(useAttemptStore.getState().timeRemainingSeconds).toBe(96);
  });

  it('does not tick when status is NOT_ATTEMPTED or SUBMITTED', () => {
    useAttemptStore.getState().setAllState({
      status: 'NOT_ATTEMPTED',
      timeRemainingSeconds: 100,
    });

    renderHook(() => useExamTimer());

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(useAttemptStore.getState().timeRemainingSeconds).toBe(100);
  });

  it('clamps return value to 0 if time is 0 or negative', () => {
    useAttemptStore.getState().setAllState({
      status: 'IN_PROGRESS',
      timeRemainingSeconds: 0,
    });

    const { result } = renderHook(() => useExamTimer());

    expect(result.current.timeRemainingSeconds).toBe(0);
  });
});
