/**
 * @vitest-environment jsdom
 */
import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import {
  BackendAvailabilityProvider,
  useBackendAvailability,
} from "@/context/backend-availability-context";
import { BackendStatusBanner } from "@/components/ui/BackendStatusBanner";

function TestConsumer() {
  const { status, isReady, isWaking, elapsedSeconds, retry } = useBackendAvailability();
  return (
    <div>
      <span data-testid="status">{status}</span>
      <span data-testid="ready">{String(isReady)}</span>
      <span data-testid="waking">{String(isWaking)}</span>
      <span data-testid="elapsed">{elapsedSeconds}</span>
      <button data-testid="retry-btn" onClick={() => retry()}>
        Retry
      </button>
    </div>
  );
}

describe("ExamArena BackendAvailabilityProvider & Banner", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval"] });
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("transitions to ready when /api/health/ready responds with 200 connected", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        status: "ready",
        database: "connected",
        redis: "connected",
      }),
    });
    global.fetch = fetchMock;

    render(
      <BackendAvailabilityProvider>
        <TestConsumer />
        <BackendStatusBanner />
      </BackendAvailabilityProvider>
    );

    await act(async () => {
      await Promise.resolve();
    });

    expect(screen.getByTestId("status").textContent).toBe("ready");
    expect(screen.getByTestId("ready").textContent).toBe("true");
  });

  it("transitions to waking when backend is warming from cold start", async () => {
    let resolveReady: (value: any) => void;
    const readyPromise = new Promise((res) => {
      resolveReady = res;
    });

    const fetchMock = vi.fn().mockImplementation(() => readyPromise);
    global.fetch = fetchMock;

    render(
      <BackendAvailabilityProvider>
        <TestConsumer />
        <BackendStatusBanner />
      </BackendAvailabilityProvider>
    );

    act(() => {
      vi.advanceTimersByTime(2000);
    });

    expect(screen.getByTestId("status").textContent).toBe("waking");
    expect(screen.getByTestId("waking").textContent).toBe("true");

    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(parseInt(screen.getByTestId("elapsed").textContent || "0", 10)).toBeGreaterThanOrEqual(4);

    await act(async () => {
      resolveReady!({
        ok: true,
        status: 200,
        json: async () => ({ status: "ready", database: "connected", redis: "connected" }),
      });
      await Promise.resolve();
    });

    await act(async () => {
      vi.advanceTimersByTime(3000);
      await Promise.resolve();
    });

    expect(screen.getByTestId("status").textContent).toBe("ready");
  });
});
