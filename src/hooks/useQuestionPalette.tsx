import { useAttemptStore } from '@/stores/useAttemptStore';
import { useCallback } from 'react';
import { SelectedOptionCreate } from '@/types/attempt';

export function useQuestionPalette() {
  const store = useAttemptStore();
  const answers = store.answers;

  const setActiveQuestion = useCallback((questionId: string) => {
    // When setting active, if it's NOT_VISITED, it becomes VISITED_NOT_ANSWERED
    if (answers[questionId] && answers[questionId].status === "NOT_VISITED") {
      store.setAnswerState(questionId, { status: "VISITED_NOT_ANSWERED" });
    }
    store.setAllState({ activeQuestionId: questionId });
  }, [answers, store]);

  const updateAnswer = useCallback((questionId: string, textAnswer?: string, selectedOptions?: SelectedOptionCreate[]) => {
    const q = answers[questionId];
    if (!q) return;

    const hasAnswer = (textAnswer != null && textAnswer.trim() !== '') || 
                      (selectedOptions != null && selectedOptions.length > 0);

    // Keep 'MARKED_FOR_REVIEW' if it was marked. Only change to ANSWERED if it was not marked.
    let newStatus = q.status;
    if (hasAnswer) {
      if (q.status !== "MARKED_FOR_REVIEW") {
        newStatus = "ANSWERED";
      }
    } else {
      if (q.status !== "MARKED_FOR_REVIEW") {
        newStatus = "VISITED_NOT_ANSWERED";
      }
    }

    store.setAnswerState(questionId, {
      textAnswer: textAnswer !== undefined ? textAnswer : q.textAnswer,
      selectedOptions: selectedOptions !== undefined ? selectedOptions : q.selectedOptions,
      status: newStatus,
    });
  }, [answers, store]);

  const markQuestionForReview = useCallback((questionId: string) => {
    store.setAnswerState(questionId, { status: "MARKED_FOR_REVIEW" });
  }, [store]);

  const unmarkQuestionForReview = useCallback((questionId: string) => {
    const q = answers[questionId];
    if (q) {
      const hasAnswer = (q.textAnswer != null && q.textAnswer.trim() !== '') || 
                        (q.selectedOptions != null && q.selectedOptions.length > 0);
      store.setAnswerState(questionId, {
        status: hasAnswer ? "ANSWERED" : "VISITED_NOT_ANSWERED"
      });
    }
  }, [answers, store]);

  return {
    setActiveQuestion,
    updateAnswer,
    markQuestionForReview,
    unmarkQuestionForReview
  };
}
