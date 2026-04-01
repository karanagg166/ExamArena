import * as React from "react";
import { cn } from "@/lib/utils";
import { type LucideIcon, Inbox } from "lucide-react";

interface EmptyStateProps {
  /** Lucide icon OR custom JSX */
  icon?: LucideIcon | React.ReactNode;
  /** Main message */
  title: string;
  /** Description text */
  description?: string;
  /** Optional action button/link */
  action?: React.ReactNode;
  /** Additional className */
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  const isComponent = typeof icon === "function";
  const Icon = (isComponent ? icon : Inbox) as LucideIcon;

  return (
    <div
      className={cn(
        "flex min-h-[30vh] flex-col items-center justify-center gap-4 px-4 py-12 text-center animate-fade-in",
        className
      )}
    >
      <div className="rounded-2xl bg-[var(--surface-2)] p-4 flex items-center justify-center">
        {icon ? (
          isComponent ? (
            <Icon className="h-8 w-8 text-[var(--text-muted)]" />
          ) : (
            icon
          )
        ) : (
          <Inbox className="h-8 w-8 text-[var(--text-muted)]" />
        )}
      </div>

      <div className="max-w-sm space-y-1.5">
        <h3 className="text-base font-semibold text-[var(--text-primary)]">
          {title}
        </h3>

        {description && (
          <p className="text-sm text-[var(--text-muted)]">
            {description}
          </p>
        )}
      </div>

      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}