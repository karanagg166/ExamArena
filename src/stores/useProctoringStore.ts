import { create } from "zustand";

export interface ProctoringViolation {
  id: string;
  timestamp: string;
  reason: string;
}

interface ProctoringState {
  warningCount: number;
  maxWarnings: number;
  isFullscreen: boolean;
  violations: ProctoringViolation[];
  isTerminated: boolean;
  terminationReason: string | null;
  isProctoringActive: boolean;

  recordWarning: (reason: string) => { warningCount: number; maxReached: boolean };
  setFullscreen: (val: boolean) => void;
  setProctoringActive: (val: boolean) => void;
  terminateAttempt: (reason: string) => void;
  reset: (maxWarnings?: number) => void;
}

const DEFAULT_MAX_WARNINGS = 3;

export const useProctoringStore = create<ProctoringState>((set, get) => ({
  warningCount: 0,
  maxWarnings: DEFAULT_MAX_WARNINGS,
  isFullscreen: false,
  violations: [],
  isTerminated: false,
  terminationReason: null,
  isProctoringActive: false,

  recordWarning: (reason: string) => {
    const state = get();
    const newCount = state.warningCount + 1;
    const maxReached = newCount >= state.maxWarnings;

    const violation: ProctoringViolation = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      timestamp: new Date().toISOString(),
      reason,
    };

    set({
      warningCount: newCount,
      violations: [...state.violations, violation],
      isTerminated: maxReached ? true : state.isTerminated,
      terminationReason: maxReached
        ? `Exceeded maximum allowable proctoring violations (${state.maxWarnings}).`
        : state.terminationReason,
    });

    return { warningCount: newCount, maxReached };
  },

  setFullscreen: (isFullscreen: boolean) => set({ isFullscreen }),

  setProctoringActive: (isProctoringActive: boolean) => set({ isProctoringActive }),

  terminateAttempt: (terminationReason: string) =>
    set({ isTerminated: true, terminationReason, isProctoringActive: false }),

  reset: (maxWarnings = DEFAULT_MAX_WARNINGS) =>
    set({
      warningCount: 0,
      maxWarnings,
      isFullscreen: false,
      violations: [],
      isTerminated: false,
      terminationReason: null,
      isProctoringActive: false,
    }),
}));
