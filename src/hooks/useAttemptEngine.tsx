import { useAttemptStore } from '@/stores/useAttemptStore';
import { useQuestionPalette } from './useQuestionPalette';
import { useExamTimer } from './useExamTimer';
import { useExamLifeCycle } from './useExamLifeCycle';

// Facade combining all hooks for backward compatibility and clean UI usage
export function useAttemptEngine() {
  const store = useAttemptStore();
  const palette = useQuestionPalette();
  const timer = useExamTimer();
  const lifecycle = useExamLifeCycle();

  return {
    // State
    examId: store.examId,
    attemptId: store.attemptId,
    answers: store.answers,
    status: store.status,
    startedAt: store.startedAt,
    activeQuestionId: store.activeQuestionId,
    timeRemainingSeconds: timer.timeRemainingSeconds,

    // Orchestrated Actions
    initializeAttempt: lifecycle.initializeAttempt,
    setActiveQuestion: palette.setActiveQuestion,
    updateAnswer: palette.updateAnswer,
    markQuestionForReview: palette.markQuestionForReview,
    unmarkQuestionForReview: palette.unmarkQuestionForReview,
    decrementTime: timer.decrementTime,
    submitAttemptLocal: lifecycle.submitAttemptLocal,
    clearAttempt: lifecycle.clearAttemptLocal,
  };
}
