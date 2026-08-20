import React, { useEffect, useRef } from 'react';
import { useAttemptEngine } from '@/hooks/useAttemptEngine';
import { Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ExamTimerProps {
  examId?: string;
  durationMinutes?: number;
  onTimeUp: () => void;
}

export const ExamTimer = ({ durationMinutes, onTimeUp }: ExamTimerProps) => {
  const { timeRemainingSeconds, status } = useAttemptEngine();
  const hasCalledTimeUp = useRef(false);

  useEffect(() => {
    if (status !== 'IN_PROGRESS') return;
    if (timeRemainingSeconds === null) return;

    if (timeRemainingSeconds <= 0 && !hasCalledTimeUp.current) {
      hasCalledTimeUp.current = true;
      onTimeUp();
      return;
    }
  }, [timeRemainingSeconds, status, onTimeUp]);

  // Fallback to durationMinutes if timeRemainingSeconds is not yet loaded while in progress
  const displaySeconds = timeRemainingSeconds ?? (status === 'IN_PROGRESS' && durationMinutes ? durationMinutes * 60 : null);

  if (displaySeconds === null) {
    return null;
  }

  const safeTime = Math.max(0, displaySeconds);
  const hours = Math.floor(safeTime / 3600);
  const minutes = Math.floor((safeTime % 3600) / 60);
  const seconds = safeTime % 60;

  const isWarning = safeTime < 300 && safeTime > 60; // less than 5 mins
  const isCritical = safeTime <= 60; // less than 1 min

  return (
    <div 
      role="timer"
      aria-label="Exam Time Remaining"
      className={cn(
        "flex items-center gap-2 px-3 py-1.5 rounded-lg font-mono font-semibold text-sm md:text-base border shrink-0 transition-colors shadow-sm",
        isCritical
          ? "bg-red-500/15 border-red-500/50 text-red-400 animate-pulse"
          : isWarning 
            ? "bg-amber-500/10 border-amber-500/30 text-amber-400" 
            : "bg-white/5 border-white/10 text-white"
      )}
    >
      <Clock className={cn("w-4 h-4 shrink-0", isCritical ? "text-red-400" : isWarning ? "text-amber-400" : "text-indigo-400")} />
      <span className="hidden sm:inline-block text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-sans mr-0.5">Time:</span>
      <div className="flex items-center">
        {hours > 0 && <span>{hours.toString().padStart(2, '0')}:</span>}
        <span>{minutes.toString().padStart(2, '0')}:</span>
        <span>{seconds.toString().padStart(2, '0')}</span>
      </div>
    </div>
  );
};
