import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold transition-all active:scale-[0.98] disabled:pointer-events-none disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--background)]",
  {
    variants: {
      variant: {
        primary:
          "bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] focus-visible:ring-[var(--accent)] shadow-[var(--shadow-sm)]",
        secondary:
          "bg-[var(--surface-2)] text-[var(--text-primary)] hover:bg-[var(--surface-3)] focus-visible:ring-[var(--accent)]",
        ghost:
          "text-[var(--text-secondary)] hover:bg-[var(--surface-2)] hover:text-[var(--text-primary)] focus-visible:ring-[var(--accent)]",
        danger:
          "bg-[var(--error)] text-white hover:brightness-110 focus-visible:ring-[var(--error)]",
        success:
          "bg-[var(--success)] text-white hover:brightness-110 focus-visible:ring-[var(--success)]",
        outline:
          "border border-[var(--border-default)] text-[var(--text-secondary)] hover:bg-[var(--surface-2)] hover:text-[var(--text-primary)] focus-visible:ring-[var(--accent)]",
      },
      size: {
        sm: "h-9 px-3",
        md: "h-10 px-4",
        lg: "h-11 px-5",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  },
);

export interface ButtonProps
  extends
    React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        ref={ref}
        className={cn(buttonVariants({ variant, size }), className)}
        {...props}
      />
    );
  },
);

Button.displayName = "Button";
