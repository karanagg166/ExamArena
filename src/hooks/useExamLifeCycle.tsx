import { useCallback } from 'react';
import { useAttemptStore, QuestionAttemptState } from '@/stores/useAttemptStore';
import { api } from '@/lib/axios';

export function useExamLifeCycle() {
  const store = useAttemptStore();

  const initializeAttempt = useCallback((examId: string, attemptId: string, initialAnswers: any[], startedAt: string, defaultTimeLimitSeconds?: number) => {
    // Only initialize if we're starting a new attempt or forcing a refresh of the SAME attempt.
    if (store.attemptId === attemptId && Object.keys(store.answers).length > 0) {
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
        selectedOptions: ans.selectedOptions?.map((o: any) => ({ optionId: o.optionId })) || [],
      };
      if (ans.textAnswer || (ans.selectedOptions && ans.selectedOptions.length > 0)) {
         newAnswers[ans.questionId].status = "ANSWERED";
      }
    });

    const firstQ = initialAnswers.length > 0 ? initialAnswers[0].questionId : null;
    if (firstQ && newAnswers[firstQ] && newAnswers[firstQ].status === "NOT_VISITED") {
        newAnswers[firstQ].status = "VISITED_NOT_ANSWERED";
    }

    store.setAllState({
      examId,
      attemptId,
      answers: newAnswers,
      status: "IN_PROGRESS",
      startedAt,
      activeQuestionId: firstQ,
      timeRemainingSeconds: defaultTimeLimitSeconds || null,
    });
  }, [store]);

  const submitAttemptLocal = useCallback(() => {
    store.setAllState({ status: "SUBMITTED" });
  }, [store]);

  const clearAttemptLocal = useCallback(() => {
    store.clearAttempt();
  }, [store]);

  return {
    initializeAttempt,
    submitAttemptLocal,
    clearAttemptLocal
  };
}
