import { useEffect } from 'react';
import { useAttemptStore } from '@/stores/useAttemptStore';

export function useExamTimer() {
  const store = useAttemptStore();
  const timeRemainingSeconds = store.timeRemainingSeconds;
  
  useEffect(() => {
    if (store.status !== "IN_PROGRESS") return;

    const timer = setInterval(() => {
      const current = useAttemptStore.getState().timeRemainingSeconds;
      if (current !== null && current > 0) {
        useAttemptStore.getState().setAllState({ timeRemainingSeconds: current - 1 });
      }
    }, 1000);

    return () => clearInterval(timer);
  }, [store.status]);

  const decrementTime = () => {
    const current = useAttemptStore.getState().timeRemainingSeconds;
    if (current !== null && current > 0) {
      useAttemptStore.getState().setAllState({ timeRemainingSeconds: current - 1 });
    }
  };

  return {
    timeRemainingSeconds: timeRemainingSeconds !== null ? Math.max(0, timeRemainingSeconds) : null,
    decrementTime
  };
}
