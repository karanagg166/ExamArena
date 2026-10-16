import { describe, it, expect, beforeEach } from "vitest";
import { useProctoringStore } from "@/stores/useProctoringStore";

describe("Unit: useProctoringStore", () => {
  beforeEach(() => {
    useProctoringStore.getState().reset(3);
  });

  it("recordWarning increments count and appends violation log", () => {
    const { warningCount, maxReached } = useProctoringStore
      .getState()
      .recordWarning("Tab switch detected");

    expect(warningCount).toBe(1);
    expect(maxReached).toBe(false);
    expect(useProctoringStore.getState().violations).toHaveLength(1);
    expect(useProctoringStore.getState().violations[0].reason).toBe(
      "Tab switch detected"
    );
    expect(useProctoringStore.getState().isTerminated).toBe(false);
  });

  it("auto-terminates exam when max warnings reached", () => {
    useProctoringStore.getState().recordWarning("Violation 1");
    useProctoringStore.getState().recordWarning("Violation 2");
    const { warningCount, maxReached } = useProctoringStore
      .getState()
      .recordWarning("Violation 3");

    expect(warningCount).toBe(3);
    expect(maxReached).toBe(true);
    expect(useProctoringStore.getState().isTerminated).toBe(true);
    expect(useProctoringStore.getState().terminationReason).toContain(
      "Exceeded maximum allowable proctoring violations"
    );
  });

  it("terminateAttempt forces immediate termination", () => {
    useProctoringStore.getState().terminateAttempt("Multiple monitors connected");

    expect(useProctoringStore.getState().isTerminated).toBe(true);
    expect(useProctoringStore.getState().terminationReason).toBe(
      "Multiple monitors connected"
    );
  });

  it("setFullscreen updates fullscreen state", () => {
    useProctoringStore.getState().setFullscreen(true);
    expect(useProctoringStore.getState().isFullscreen).toBe(true);

    useProctoringStore.getState().setFullscreen(false);
    expect(useProctoringStore.getState().isFullscreen).toBe(false);
  });
});
