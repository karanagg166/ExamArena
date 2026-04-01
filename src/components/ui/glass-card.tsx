import * as React from "react";
import { cn } from "@/lib/utils";

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Enable hover lift + glow effect */
  interactive?: boolean;
  /** Padding preset */
  padding?: "none" | "sm" | "md" | "lg";
}

const paddingMap = {
  none: "",
  sm: "p-4",
  md: "p-5 md:p-6",
  lg: "p-6 md:p-8",
};

export function GlassCard({
  className,
  interactive = false,
  padding = "md",
  children,
  ...props
}: GlassCardProps) {
  return (
    <div
      className={cn(
        "glass-card",
        paddingMap[padding],
        !interactive && "hover:transform-none hover:shadow-[var(--shadow-md)]",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
