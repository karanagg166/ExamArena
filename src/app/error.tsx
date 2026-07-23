"use client";

import { ErrorUI } from "@/components/ui/error-ui";

export default function RootError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <ErrorUI
      error={error}
      reset={reset}
      title="Application Error"
      subtitle="An unexpected error occurred while loading this page."
    />
  );
}
