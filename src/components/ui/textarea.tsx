import * as React from "react";
import { cn } from "@/lib/utils";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => {
  return (
    <textarea
      ref={ref}
      className={cn(
        "min-h-24 w-full rounded-xl border border-[var(--border-default)] bg-[rgba(255,255,255,0.04)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-dimmed)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:border-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50 transition-all",
        className,
      )}
      {...props}
    />
  );
});

Textarea.displayName = "Textarea";
