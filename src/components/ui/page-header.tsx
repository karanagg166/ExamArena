import * as React from "react";
import { cn } from "@/lib/utils";

interface PageHeaderProps {
  /** Page title */
  title: string;
  /** Optional subtitle / description */
  subtitle?: string;
  /** Optional alias for subtitle (for flexibility) */
  description?: string;
  /** Optional overline text (small label above title) */
  overline?: string;
  /** Right-side actions (buttons, badges, etc.) */
  actions?: React.ReactNode;
  /** Additional className */
  className?: string;
}

export function PageHeader({
  title,
  subtitle,
  description,
  overline,
  actions,
  className,
}: PageHeaderProps) {
  const text = subtitle || description;

  return (
    <header
      className={cn(
        "flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between",
        className
      )}
    >
      <div className="space-y-1">
        {overline && (
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {overline}
          </p>
        )}

        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight leading-tight">
          {title}
        </h1>

        {text && (
          <p className="text-muted-foreground text-sm sm:text-base">
            {text}
          </p>
        )}
      </div>

      {actions && (
        <div className="flex shrink-0 items-center gap-2">
          {actions}
        </div>
      )}
    </header>
  );
}