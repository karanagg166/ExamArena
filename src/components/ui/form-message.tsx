import { cn } from "@/lib/utils";

type FormMessageProps = {
  message?: string;
  type?: "success" | "error" | "info";
  className?: string;
};

export function FormMessage({
  message,
  type = "info",
  className,
}: FormMessageProps) {
  if (!message) {
    return null;
  }

  const toneClass =
    type === "success"
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
      : type === "error"
        ? "border-red-500/30 bg-red-500/10 text-red-300"
        : "border-indigo-500/30 bg-indigo-500/10 text-indigo-300";

  return (
    <div
      className={cn(
        "rounded-xl border px-3 py-2 text-sm",
        toneClass,
        className,
      )}
    >
      {message}
    </div>
  );
}
