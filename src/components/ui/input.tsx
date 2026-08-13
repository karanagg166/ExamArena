import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  containerClassName?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", error, containerClassName, ...props }, ref) => {
    return (
      <div className={cn("w-full", containerClassName)}>
        <input
          ref={ref}
          type={type}
          className={cn(
            "flex h-10 w-full rounded-xl border border-[var(--border-default)] bg-[rgba(255,255,255,0.04)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-dimmed)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:border-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50 transition-all",
            error && "border-red-500/80 text-red-100 ring-1 ring-red-500/40 focus-visible:ring-red-500 focus-visible:border-red-500",
            className,
          )}
          {...props}
        />
        {error && (
          <p className="text-xs font-medium text-red-400 mt-1 animate-in fade-in-50 duration-150">
            {error}
          </p>
        )}
      </div>
    );
  },
);

Input.displayName = "Input";

