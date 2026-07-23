"use client";

import { ErrorUI } from "@/components/ui/error-ui";

export default function TeacherError({
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
      title="Teacher Portal Error"
      subtitle="An error occurred in the teacher section."
    />
  );
}
