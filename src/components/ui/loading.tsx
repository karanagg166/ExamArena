import { cn } from "@/lib/utils";

export function Spinner({ className }: { className?: string }) {
    return <div className={cn("h-6 w-6 animate-spin rounded-full border-2 border-indigo-400/30 border-t-indigo-400", className)} />;
}

export function Skeleton({ className }: { className?: string }) {
    return <div className={cn("animate-pulse rounded-md bg-zinc-800", className)} />;
}
