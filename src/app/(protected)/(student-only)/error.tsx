"use client";

import { ErrorUI } from "@/components/ui/error-ui";

export default function StudentError({
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
      title="Student Portal Error"
      subtitle="An error occurred in the student section."
    />
  );
}
