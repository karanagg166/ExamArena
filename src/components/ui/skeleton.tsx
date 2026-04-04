import * as React from "react";
import { cn } from "@/lib/utils";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Make it a circle (for avatars) */
  circle?: boolean;
}

/** Base skeleton shimmer element */
export function Skeleton({ className, circle, ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        "skeleton",
        circle ? "aspect-square rounded-full" : "h-4 w-full",
        className,
      )}
      {...props}
    />
  );
}

/** Pre-built skeleton for a stat card */
export function StatCardSkeleton() {
  return (
    <div className="glass-card p-5 md:p-6 space-y-3">
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-8 w-32" />
        </div>
        <Skeleton className="h-10 w-10 rounded-xl" />
      </div>
      <Skeleton className="h-3 w-40" />
    </div>
  );
}

/** Pre-built skeleton for a card in a grid */
export function CardSkeleton() {
  return (
    <div className="glass-card p-5 space-y-4">
      <div className="flex items-center gap-3">
        <Skeleton circle className="h-10 w-10" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </div>
      <div className="space-y-2">
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-5/6" />
      </div>
    </div>
  );
}

/** Pre-built skeleton for a table row */
export function TableRowSkeleton({ cols = 4 }: { cols?: number }) {
  return (
    <div className="flex items-center gap-4 px-4 py-3">
      {Array.from({ length: cols }).map((_, i) => (
        <Skeleton key={i} className={cn("h-4", i === 0 ? "w-1/3" : "w-1/5")} />
      ))}
    </div>
  );
}

/** Pre-built skeleton for a page header */
export function PageHeaderSkeleton() {
  return (
    <div className="space-y-2">
      <Skeleton className="h-3 w-20" />
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-4 w-96" />
    </div>
  );
}
