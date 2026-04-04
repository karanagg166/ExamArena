import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { AttemptStatus, SelectedOptionCreate } from '@/types/attempt';
import { QuestionType } from '@/types/question';

// Extended status to include marked and not visited
export type ExtendedQuestionStatus = "NOT_VISITED" | "VISITED_NOT_ANSWERED" | "ANSWERED" | "MARKED_FOR_REVIEW";

export interface QuestionAttemptState {
  id: string; // The database id of the StudentExamAnswer
  questionId: string;
  questionType: QuestionType;
  status: ExtendedQuestionStatus;
  textAnswer?: string;
  selectedOptions?: SelectedOptionCreate[]; // Changed to match schema
}

export interface AttemptStoreState {
  examId: string | null;
  attemptId: string | null;
  answers: Record<string, QuestionAttemptState>; // Indexed by questionId
  status: AttemptStatus;
  startedAt: string | null;
  activeQuestionId: string | null;
  timeRemainingSeconds: number | null;
  
  // Actions
  setAllState: (state: Partial<AttemptStoreState>) => void;
  setAnswerState: (questionId: string, state: Partial<QuestionAttemptState>) => void;
  clearAttempt: () => void;
}

export const useAttemptStore = create<AttemptStoreState>()(
  persist(
    (set) => ({
      examId: null,
      attemptId: null,
      answers: {},
      status: "NOT_ATTEMPTED",
      startedAt: null,
      activeQuestionId: null,
      timeRemainingSeconds: null,

      setAllState: (newState) => set((state) => ({ ...state, ...newState })),
      
      setAnswerState: (questionId, newQState) => set((state) => {
        const answers = { ...state.answers };
        if (answers[questionId]) {
          answers[questionId] = { ...answers[questionId], ...newQState };
        }
        return { answers };
      }),

      clearAttempt: () => set(() => ({
        examId: null,
        attemptId: null,
        answers: {},
        status: "NOT_ATTEMPTED",
        startedAt: null,
        activeQuestionId: null,
        timeRemainingSeconds: null,
      })),
    }),
    {
      name: 'exam-attempt-storage', // key in localStorage
    }
  )
);
