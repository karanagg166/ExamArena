import React, { useEffect, useRef } from 'react';
import { useAttemptEngine } from '@/hooks/useAttemptEngine';
import { Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

export const ExamTimer = ({ examId, onTimeUp }: { examId: string, onTimeUp: () => void }) => {
  const { timeRemainingSeconds, decrementTime, status } = useAttemptEngine();
  const hasCalledTimeUp = useRef(false);

  useEffect(() => {
    if (status !== 'IN_PROGRESS' || timeRemainingSeconds === null) return;

    if (timeRemainingSeconds <= 0 && !hasCalledTimeUp.current) {
      hasCalledTimeUp.current = true;
      onTimeUp();
      return;
    }

    // The useExamTimer hook already ticks via its own setInterval,
    // so we do NOT add another interval here. We only watch for time-up.
  }, [timeRemainingSeconds, status, onTimeUp]);

  if (timeRemainingSeconds === null) {
      return null;
  }

  const hours = Math.floor(timeRemainingSeconds / 3600);
  const minutes = Math.floor((timeRemainingSeconds % 3600) / 60);
  const seconds = timeRemainingSeconds % 60;

  const isWarning = timeRemainingSeconds < 300; // less than 5 mins
  const isCritical = timeRemainingSeconds < 60; // less than 1 min

  return (
    <div className={cn(
        "flex items-center gap-2 px-3 py-1.5 rounded-lg font-mono font-medium text-base border shrink-0",
        isCritical
          ? "bg-red-500/15 border-red-500/50 text-red-400 animate-pulse"
          : isWarning 
            ? "bg-amber-500/10 border-amber-500/30 text-amber-400" 
            : "bg-white/5 border-white/10 text-white"
    )}>
      <Clock className={cn("w-4 h-4", isCritical ? "text-red-400" : isWarning ? "text-amber-400" : "text-indigo-400")} />
      {hours > 0 && <span>{hours.toString().padStart(2, '0')}:</span>}
      <span>{minutes.toString().padStart(2, '0')}:</span>
      <span>{seconds.toString().padStart(2, '0')}</span>
    </div>
  );
};
