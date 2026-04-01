import * as React from "react";
import { cn } from "@/lib/utils";
import { type LucideIcon } from "lucide-react";

interface StatCardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Title label */
  label: string;
  /** Main stat value */
  value: string | number;
  /** Optional description or change indicator */
  description?: string;
  /** Lucide icon component */
  icon?: LucideIcon;
  /** Trend direction for styling */
  trend?: "up" | "down" | "neutral";
}

export function StatCard({
  label,
  value,
  description,
  icon: Icon,
  trend,
  className,
  ...props
}: StatCardProps) {
  return (
    <div
      className={cn(
        "glass-card p-5 md:p-6 group",
        className,
      )}
      {...props}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-[var(--text-muted)]">
            {label}
          </p>
          <p className="text-2xl font-bold tracking-tight text-[var(--text-primary)] md:text-3xl">
            {value}
          </p>
        </div>
        {Icon && (
          <div className="rounded-xl bg-[var(--accent-muted)] p-2.5 text-[var(--accent)] transition-colors group-hover:bg-[var(--accent)] group-hover:text-white">
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
      {description && (
        <p
          className={cn(
            "mt-3 text-sm",
            trend === "up" && "text-[var(--success)]",
            trend === "down" && "text-[var(--error)]",
            !trend && "text-[var(--text-muted)]",
          )}
        >
          {trend === "up" && "↑ "}
          {trend === "down" && "↓ "}
          {description}
        </p>
      )}
    </div>
  );
}
