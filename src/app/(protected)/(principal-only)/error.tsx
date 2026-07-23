"use client";

import { ErrorUI } from "@/components/ui/error-ui";

export default function PrincipalError({
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
      title="Principal Portal Error"
      subtitle="An error occurred in the principal management area."
    />
  );
}
