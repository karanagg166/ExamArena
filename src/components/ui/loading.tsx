import { cn } from "@/lib/utils";

export function Spinner({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "h-6 w-6 animate-spin rounded-full border-2 border-[var(--accent-muted)] border-t-[var(--accent)]",
        className,
      )}
    />
  );
}

/** @deprecated Use Skeleton from @/components/ui/skeleton instead */
export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={cn("skeleton h-4", className)} />
  );
}
