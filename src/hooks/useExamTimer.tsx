import { useEffect, useState, useCallback } from 'react';
import { useAttemptStore } from '@/stores/useAttemptStore';

export function useExamTimer() {
  const store = useAttemptStore();

  const calculateRemaining = useCallback(() => {
    const { startedAt, durationSeconds, timeRemainingSeconds } = useAttemptStore.getState();
    if (startedAt && durationSeconds && durationSeconds > 0) {
      const startTime = new Date(startedAt).getTime();
      const now = Date.now();
      const elapsedSeconds = Math.floor((now - startTime) / 1000);
      return Math.max(0, durationSeconds - elapsedSeconds);
    }
    return timeRemainingSeconds !== null ? Math.max(0, timeRemainingSeconds) : null;
  }, []);

  const [remaining, setRemaining] = useState<number | null>(calculateRemaining);

  useEffect(() => {
    if (store.status !== "IN_PROGRESS") return;

    const tick = () => {
      const { startedAt, durationSeconds, timeRemainingSeconds } = useAttemptStore.getState();
      let nextRemaining: number | null = null;
      if (startedAt && durationSeconds && durationSeconds > 0) {
        const startTime = new Date(startedAt).getTime();
        const now = Date.now();
        const elapsedSeconds = Math.floor((now - startTime) / 1000);
        nextRemaining = Math.max(0, durationSeconds - elapsedSeconds);
      } else if (timeRemainingSeconds !== null && timeRemainingSeconds > 0) {
        nextRemaining = Math.max(0, timeRemainingSeconds - 1);
      } else if (timeRemainingSeconds === 0) {
        nextRemaining = 0;
      }

      setRemaining(nextRemaining);
      if (nextRemaining !== null) {
        useAttemptStore.getState().setAllState({ timeRemainingSeconds: nextRemaining });
      }
    };

    const timer = setInterval(tick, 1000);

    return () => clearInterval(timer);
  }, [store.status, store.startedAt, store.durationSeconds]);

  return {
    timeRemainingSeconds: remaining,
    decrementTime: () => {},
  };
}
