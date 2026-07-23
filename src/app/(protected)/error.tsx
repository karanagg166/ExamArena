"use client";

import { ErrorUI } from "@/components/ui/error-ui";

export default function ProtectedError({
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
      title="Dashboard Error"
      subtitle="Failed to load requested resource or section."
    />
  );
}
