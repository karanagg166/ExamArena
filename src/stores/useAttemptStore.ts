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
  isDirty?: boolean;
  modifiedAt?: number;
}

export interface AttemptStoreState {
  userId: string | null;
  examId: string | null;
  attemptId: string | null;
  answers: Record<string, QuestionAttemptState>; // Indexed by questionId
  status: AttemptStatus;
  startedAt: string | null;
  durationSeconds: number | null;
  activeQuestionId: string | null;
  timeRemainingSeconds: number | null;
  draftRevision: number;
  warningCount: number;
  
  // Actions
  setAllState: (state: Partial<AttemptStoreState>) => void;
  setAnswerState: (questionId: string, state: Partial<QuestionAttemptState>, markDirty?: boolean) => void;
  markAnswersSaved: (savedBeforeTimestamp?: number) => void;
  clearAttempt: () => void;
}

export const useAttemptStore = create<AttemptStoreState>()(
  persist(
    (set) => ({
      userId: null,
      examId: null,
      attemptId: null,
      answers: {},
      status: "NOT_ATTEMPTED",
      startedAt: null,
      durationSeconds: null,
      activeQuestionId: null,
      timeRemainingSeconds: null,
      draftRevision: 0,
      warningCount: 0,

      setAllState: (newState) => set((state) => ({ ...state, ...newState })),
      
      setAnswerState: (questionId, newQState, markDirty = true) => set((state) => {
        const answers = { ...state.answers };
        const now = Date.now();
        if (answers[questionId]) {
          answers[questionId] = {
            ...answers[questionId],
            ...newQState,
            isDirty: markDirty ? true : (newQState.isDirty ?? answers[questionId].isDirty ?? false),
            modifiedAt: markDirty ? now : answers[questionId].modifiedAt,
          };
        } else {
          answers[questionId] = {
            id: '',
            questionId,
            questionType: 'MULTIPLE_CHOICE',
            status: 'NOT_VISITED',
            ...newQState,
            isDirty: markDirty ? true : (newQState.isDirty ?? false),
            modifiedAt: markDirty ? now : undefined,
          } as QuestionAttemptState;
        }
        return { answers };
      }),

      markAnswersSaved: (savedBeforeTimestamp?: number) => set((state) => {
        const answers = { ...state.answers };
        for (const qId in answers) {
          if (answers[qId].isDirty) {
            if (!savedBeforeTimestamp || (answers[qId].modifiedAt && answers[qId].modifiedAt <= savedBeforeTimestamp)) {
              answers[qId] = { ...answers[qId], isDirty: false };
            }
          }
        }
        return { answers };
      }),

      clearAttempt: () => set(() => ({
        userId: null,
        examId: null,
        attemptId: null,
        answers: {},
        status: "NOT_ATTEMPTED",
        startedAt: null,
        durationSeconds: null,
        activeQuestionId: null,
        timeRemainingSeconds: null,
        draftRevision: 0,
        warningCount: 0,
      })),
    }),
    {
      name: 'exam-attempt-storage', // key in localStorage
    }
  )
);
