"use client";

import { ErrorUI } from "@/components/ui/error-ui";

export default function PublicError({
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
      title="Page Error"
      subtitle="Something went wrong while loading this page."
    />
  );
}
