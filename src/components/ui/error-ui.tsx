"use client";

import { useEffect } from "react";
import * as Sentry from "@sentry/nextjs";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";

export interface ErrorUIProps {
  error: Error & { digest?: string };
  reset?: () => void;
  title?: string;
  subtitle?: string;
}

export function ErrorUI({
  error,
  reset,
  title = "Something went wrong",
  subtitle = "An unexpected error occurred while rendering this page.",
}: ErrorUIProps) {
  useEffect(() => {
    // Log error to Sentry automatically
    console.error("Captured boundary error:", error);
    Sentry.captureException(error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] w-full items-center justify-center p-6 text-white">
      <GlassCard padding="lg" className="w-full max-w-lg text-center shadow-2xl border-red-500/20 bg-zinc-950/80">
        <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400">
          <AlertTriangle className="h-8 w-8 animate-pulse" />
        </div>

        <h2 className="text-2xl font-bold tracking-tight text-white">{title}</h2>
        <p className="mt-2 text-sm text-zinc-400">{subtitle}</p>

        {error?.message && (
          <div className="mt-4 rounded-xl border border-red-900/40 bg-red-950/30 p-3 text-xs font-mono text-red-300 text-left overflow-auto max-h-32">
            {error.message}
          </div>
        )}

        {error?.digest && (
          <p className="mt-2 text-[11px] font-mono text-zinc-500">
            Error ID: {error.digest}
          </p>
        )}

        <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-3">
          {reset && (
            <Button
              onClick={() => reset()}
              className="w-full sm:w-auto bg-indigo-600 hover:bg-indigo-500 text-white"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Try Again
            </Button>
          )}
          <Button
            variant="secondary"
            className="w-full sm:w-auto border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-200"
            onClick={() => {
              window.location.href = "/";
            }}
          >
            <Home className="mr-2 h-4 w-4" />
            Go to Home
          </Button>
        </div>
      </GlassCard>
    </div>
  );
}

export default ErrorUI;
