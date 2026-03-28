import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
    "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold transition-all disabled:pointer-events-none disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-black",
    {
        variants: {
            variant: {
                primary: "bg-indigo-600 text-white hover:bg-indigo-500 focus-visible:ring-indigo-500",
                secondary: "bg-zinc-800 text-zinc-100 hover:bg-zinc-700 focus-visible:ring-zinc-500",
                ghost: "text-zinc-300 hover:bg-zinc-800 hover:text-white focus-visible:ring-zinc-500",
                danger: "bg-red-600 text-white hover:bg-red-500 focus-visible:ring-red-500",
                success: "bg-emerald-600 text-white hover:bg-emerald-500 focus-visible:ring-emerald-500",
                outline: "border border-zinc-700 text-zinc-200 hover:bg-zinc-800 focus-visible:ring-zinc-500",
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
    }
);

export interface ButtonProps
    extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
    asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant, size, asChild = false, ...props }, ref) => {
        const Comp = asChild ? Slot : "button";
        return <Comp ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />;
    }
);

Button.displayName = "Button";
