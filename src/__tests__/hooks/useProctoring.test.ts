import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useProctoring } from '@/hooks/useProctoring';

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

    // Mock document.hidden
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
});
