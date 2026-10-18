import { useCallback } from 'react';
import { useAttemptStore, QuestionAttemptState } from '@/stores/useAttemptStore';
import type { QuestionType } from '@/types';

export function useExamLifeCycle() {
  const setAllState = useAttemptStore((s) => s.setAllState);
  const clearAttempt = useAttemptStore((s) => s.clearAttempt);

  const initializeAttempt = useCallback((examId: string, attemptId: string, initialAnswers: { id: string; questionId: string; questionType: QuestionType; textAnswer?: string; selectedOptions?: { optionId: string }[] }[], startedAt: string, defaultTimeLimitSeconds?: number) => {
    const currentState = useAttemptStore.getState();
    // Only initialize if we're starting a new attempt or forcing a refresh of the SAME attempt.
    if (currentState.attemptId === attemptId && Object.keys(currentState.answers).length > 0) {
      if ((!currentState.durationSeconds || currentState.timeRemainingSeconds === null) && defaultTimeLimitSeconds) {
        setAllState({
          durationSeconds: defaultTimeLimitSeconds,
          timeRemainingSeconds: currentState.timeRemainingSeconds ?? defaultTimeLimitSeconds,
          startedAt: currentState.startedAt || startedAt,
        });
      }
      return; 
    }

    const newAnswers: Record<string, QuestionAttemptState> = {};
    initialAnswers.forEach((ans) => {
      newAnswers[ans.questionId] = {
        id: ans.id,
        questionId: ans.questionId,
        questionType: ans.questionType,
        status: "NOT_VISITED",
        textAnswer: ans.textAnswer,
        selectedOptions: ans.selectedOptions?.map((o: { optionId: string }) => ({ optionId: o.optionId })) || [],
      };
      if (ans.textAnswer || (ans.selectedOptions && ans.selectedOptions.length > 0)) {
         newAnswers[ans.questionId].status = "ANSWERED";
      }
    });

    const firstQ = initialAnswers.length > 0 ? initialAnswers[0].questionId : null;
    if (firstQ && newAnswers[firstQ] && newAnswers[firstQ].status === "NOT_VISITED") {
        newAnswers[firstQ].status = "VISITED_NOT_ANSWERED";
    }

    setAllState({
      examId,
      attemptId,
      answers: newAnswers,
      status: "IN_PROGRESS",
      startedAt,
      durationSeconds: defaultTimeLimitSeconds || null,
      activeQuestionId: firstQ,
      timeRemainingSeconds: defaultTimeLimitSeconds || null,
    });
  }, [setAllState]);

  const submitAttemptLocal = useCallback(() => {
    setAllState({ status: "SUBMITTED" });
  }, [setAllState]);

  const clearAttemptLocal = useCallback(() => {
    clearAttempt();
  }, [clearAttempt]);

  return {
    initializeAttempt,
    submitAttemptLocal,
    clearAttemptLocal
  };
}
