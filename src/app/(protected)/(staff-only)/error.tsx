"use client";

import { ErrorUI } from "@/components/ui/error-ui";

export default function StaffError({
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
      title="Staff Portal Error"
      subtitle="An error occurred in the staff portal area."
    />
  );
}
