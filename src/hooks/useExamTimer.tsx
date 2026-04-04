import { useEffect } from 'react';
import { useAttemptStore } from '@/stores/useAttemptStore';

export function useExamTimer() {
  const store = useAttemptStore();
  const timeRemainingSeconds = store.timeRemainingSeconds;
  
  useEffect(() => {
    if (timeRemainingSeconds === null || timeRemainingSeconds <= 0 || store.status !== "IN_PROGRESS") {
      return;
    }

    const timer = setInterval(() => {
      store.setAllState({ timeRemainingSeconds: timeRemainingSeconds - 1 });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeRemainingSeconds, store]);

  const decrementTime = () => {
    if (timeRemainingSeconds !== null && timeRemainingSeconds > 0) {
      store.setAllState({ timeRemainingSeconds: timeRemainingSeconds - 1 });
    }
  };

  return {
    timeRemainingSeconds,
    decrementTime
  };
}
