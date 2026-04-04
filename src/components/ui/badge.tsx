import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default:
          "border-[rgba(99,102,241,0.2)] bg-[var(--accent-muted)] text-[var(--accent)]",
        success:
          "border-[rgba(16,185,129,0.2)] bg-[var(--success-muted)] text-[var(--success)]",
        warning:
          "border-[rgba(245,158,11,0.2)] bg-[var(--warning-muted)] text-[var(--warning)]",
        danger:
          "border-[rgba(244,63,94,0.2)] bg-[var(--error-muted)] text-[var(--error)]",
        neutral:
          "border-[var(--border-default)] bg-[var(--surface-2)] text-[var(--text-secondary)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends
    React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}
