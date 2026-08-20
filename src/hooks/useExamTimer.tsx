import { useEffect, useState, useCallback } from 'react';
import { useAttemptStore } from '@/stores/useAttemptStore';

export function useExamTimer() {
  const status = useAttemptStore((state) => state.status);
  const startedAt = useAttemptStore((state) => state.startedAt);
  const durationSeconds = useAttemptStore((state) => state.durationSeconds);
  const storeTimeRemaining = useAttemptStore((state) => state.timeRemainingSeconds);

  const calculateRemaining = useCallback(() => {
    const state = useAttemptStore.getState();
    if (state.startedAt && state.durationSeconds && state.durationSeconds > 0) {
      const startTime = new Date(state.startedAt).getTime();
      if (!isNaN(startTime)) {
        const now = Date.now();
        const elapsedSeconds = Math.floor((now - startTime) / 1000);
        return Math.max(0, state.durationSeconds - elapsedSeconds);
      }
    }
    return state.timeRemainingSeconds !== null ? Math.max(0, state.timeRemainingSeconds) : null;
  }, []);

  const [remaining, setRemaining] = useState<number | null>(calculateRemaining);

  useEffect(() => {
    if (status !== "IN_PROGRESS") return;

    const tick = () => {
      const state = useAttemptStore.getState();
      let nextRemaining: number | null = null;
      if (state.startedAt && state.durationSeconds && state.durationSeconds > 0) {
        const startTime = new Date(state.startedAt).getTime();
        if (!isNaN(startTime)) {
          const now = Date.now();
          const elapsedSeconds = Math.floor((now - startTime) / 1000);
          nextRemaining = Math.max(0, state.durationSeconds - elapsedSeconds);
        }
      } else if (state.timeRemainingSeconds !== null && state.timeRemainingSeconds > 0) {
        nextRemaining = Math.max(0, state.timeRemainingSeconds - 1);
      } else if (state.timeRemainingSeconds === 0) {
        nextRemaining = 0;
      }

      setRemaining(nextRemaining);
      if (nextRemaining !== null) {
        useAttemptStore.getState().setAllState({ timeRemainingSeconds: nextRemaining });
      }
    };

    const timer = setInterval(tick, 1000);

    return () => clearInterval(timer);
  }, [status, startedAt, durationSeconds]);

  return {
    timeRemainingSeconds: remaining ?? storeTimeRemaining,
    decrementTime: () => {},
  };
}
