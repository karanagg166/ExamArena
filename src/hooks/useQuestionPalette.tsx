import { useAttemptStore } from '@/stores/useAttemptStore';
import { useCallback } from 'react';
import { SelectedOptionCreate } from '@/types/attempt';

export function useQuestionPalette() {
  const setAnswerState = useAttemptStore((s) => s.setAnswerState);
  const setAllState = useAttemptStore((s) => s.setAllState);

  const setActiveQuestion = useCallback((questionId: string) => {
    const currentAnswers = useAttemptStore.getState().answers;
    const currentQ = currentAnswers[questionId];
    // When setting active, if it's NOT_VISITED or uninitialized, it becomes VISITED_NOT_ANSWERED
    if (!currentQ || currentQ.status === "NOT_VISITED") {
      setAnswerState(questionId, { status: "VISITED_NOT_ANSWERED" }, false);
    }
    setAllState({ activeQuestionId: questionId });
  }, [setAnswerState, setAllState]);

  const updateAnswer = useCallback((questionId: string, textAnswer?: string, selectedOptions?: SelectedOptionCreate[]) => {
    const currentAnswers = useAttemptStore.getState().answers;
    const q = currentAnswers[questionId];
    if (!q) return;

    const currentText = textAnswer !== undefined ? textAnswer : q.textAnswer;
    const currentOptions = selectedOptions !== undefined ? selectedOptions : q.selectedOptions;

    const hasAnswer = (currentText != null && currentText.trim() !== '') || 
                      (currentOptions != null && currentOptions.length > 0);

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

    setAnswerState(questionId, {
      textAnswer: currentText,
      selectedOptions: currentOptions,
      status: newStatus,
    });
  }, [setAnswerState]);

  const markQuestionForReview = useCallback((questionId: string) => {
    setAnswerState(questionId, { status: "MARKED_FOR_REVIEW" });
  }, [setAnswerState]);

  const unmarkQuestionForReview = useCallback((questionId: string) => {
    const currentAnswers = useAttemptStore.getState().answers;
    const q = currentAnswers[questionId];
    if (q) {
      const hasAnswer = (q.textAnswer != null && q.textAnswer.trim() !== '') || 
                        (q.selectedOptions != null && q.selectedOptions.length > 0);
      setAnswerState(questionId, {
        status: hasAnswer ? "ANSWERED" : "VISITED_NOT_ANSWERED"
      });
    }
  }, [setAnswerState]);

  return {
    setActiveQuestion,
    updateAnswer,
    markQuestionForReview,
    unmarkQuestionForReview
  };
}
