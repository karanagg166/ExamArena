import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useProctoring } from '@/hooks/useProctoring';
import { api } from '@/lib/axios';

vi.mock('@/lib/axios', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn().mockResolvedValue({ data: { message: 'Recorded' } }),
    put: vi.fn(),
  },
}));

describe('useProctoring', () => {
  const onWarning = vi.fn();
  const onAutoSubmit = vi.fn();
  const onFullscreenExit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('triggers warning when visibility changes to hidden', () => {
    renderHook(() =>
      useProctoring({
        maxWarnings: 3,
        onWarning,
        onAutoSubmit,
        onFullscreenExit,
        enabled: true,
      })
    );

    Object.defineProperty(document, 'hidden', { value: true, configurable: true });

    act(() => {
      document.dispatchEvent(new Event('visibilitychange'));
    });

    expect(onWarning).toHaveBeenCalledWith(1, 'Switched tab or minimized window');
  });

  it('cooldown prevents duplicate warnings within 500ms', () => {
    renderHook(() =>
      useProctoring({
        maxWarnings: 3,
        onWarning,
        onAutoSubmit,
        onFullscreenExit,
        enabled: true,
      })
    );

    Object.defineProperty(document, 'hidden', { value: true, configurable: true });

    act(() => {
      document.dispatchEvent(new Event('visibilitychange'));
      window.dispatchEvent(new Event('blur')); // Trigger blur right away
    });

    // Should only trigger once due to 500ms cooldown
    expect(onWarning).toHaveBeenCalledTimes(1);
  });

  it('triggers auto submit when max warnings reached', () => {
    vi.useFakeTimers();

    renderHook(() =>
      useProctoring({
        maxWarnings: 2,
        onWarning,
        onAutoSubmit,
        onFullscreenExit,
        enabled: true,
      })
    );

    Object.defineProperty(document, 'hidden', { value: true, configurable: true });

    // Warning 1
    act(() => {
      document.dispatchEvent(new Event('visibilitychange'));
    });
    expect(onWarning).toHaveBeenLastCalledWith(1, expect.any(String));

    // Advance past 500ms cooldown
    act(() => {
      vi.advanceTimersByTime(600);
    });

    // Warning 2 -> should trigger onAutoSubmit
    act(() => {
      document.dispatchEvent(new Event('visibilitychange'));
    });
    expect(onWarning).toHaveBeenLastCalledWith(2, expect.any(String));
    expect(onAutoSubmit).toHaveBeenCalledTimes(1);

    vi.useRealTimers();
  });

  it('invokes the latest onAutoSubmit callback without stale closure when props change', () => {
    vi.useFakeTimers();

    let capturedAnswer = 'initial answer';
    const firstSubmit = vi.fn(() => {
      // should NOT be called if updated
    });
    const secondSubmit = vi.fn(() => {
      capturedAnswer = 'updated latest answer';
    });

    const { rerender } = renderHook(
      ({ submitCb }) =>
        useProctoring({
          maxWarnings: 1,
          onWarning,
          onAutoSubmit: submitCb,
          enabled: true,
        }),
      { initialProps: { submitCb: firstSubmit } }
    );

    // Simulate answer change in parent component causing new callback definition
    rerender({ submitCb: secondSubmit });

    Object.defineProperty(document, 'hidden', { value: true, configurable: true });

    act(() => {
      document.dispatchEvent(new Event('visibilitychange'));
    });

    expect(firstSubmit).not.toHaveBeenCalled();
    expect(secondSubmit).toHaveBeenCalledTimes(1);
    expect(capturedAnswer).toBe('updated latest answer');

    vi.useRealTimers();
  });

  it('posts proctoring violations to persistent audit API when attemptId is provided', () => {
    renderHook(() =>
      useProctoring({
        maxWarnings: 3,
        attemptId: 'attempt-xyz-123',
        onWarning,
        onAutoSubmit,
        enabled: true,
      })
    );

    Object.defineProperty(document, 'hidden', { value: true, configurable: true });

    act(() => {
      document.dispatchEvent(new Event('visibilitychange'));
    });

    expect(api.post).toHaveBeenCalledWith(
      '/api/v1/attempts/attempt-xyz-123/proctoring-violation',
      expect.objectContaining({
        violationType: 'Switched tab or minimized window',
        details: expect.objectContaining({ warningCount: 1 }),
      })
    );
  });

  it('respects initialWarningCount across refresh/resume', () => {
    vi.useFakeTimers();

    const { result } = renderHook(() =>
      useProctoring({
        maxWarnings: 3,
        initialWarningCount: 2,
        onWarning,
        onAutoSubmit,
        enabled: true,
      })
    );

    expect(result.current.warningCount).toBe(2);

    Object.defineProperty(document, 'hidden', { value: true, configurable: true });

    act(() => {
      document.dispatchEvent(new Event('visibilitychange'));
    });

    // Next warning reaches 3, which is maxWarnings -> triggers auto-submit
    expect(onWarning).toHaveBeenCalledWith(3, expect.any(String));
    expect(onAutoSubmit).toHaveBeenCalledTimes(1);

    vi.useRealTimers();
  });
});

