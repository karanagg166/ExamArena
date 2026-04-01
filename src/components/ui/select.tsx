import * as React from "react";
import { cn } from "@/lib/utils";

export const Select = React.forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement>
>(({ className, children, ...props }, ref) => {
  return (
    <div className="relative">
      <select
        ref={ref}
        className={cn(
          "flex h-10 w-full appearance-none rounded-xl border border-[var(--border-default)] bg-[rgba(255,255,255,0.04)] px-3 py-2 pr-8 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-dimmed)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50 transition-all",
          className
        )}
        {...props}
      >
        {children}
      </select>
      {/* Custom Chevron Icon */}
      <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-[var(--text-muted)]">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </div>
    </div>
  );
});

Select.displayName = "Select";
