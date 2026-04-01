"use client";

import { motion, type HTMLMotionProps, type Easing } from "framer-motion";
import { cn } from "@/lib/utils";

interface PageTransitionProps extends HTMLMotionProps<"div"> {
  /** Animation variant */
  variant?: "fade" | "slideUp" | "slideRight" | "scale";
  /** Additional className */
  className?: string;
  children: React.ReactNode;
}

const variants = {
  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.3, ease: "easeOut" as Easing },
  },
  slideUp: {
    initial: { opacity: 0, y: 16 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -8 },
    transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] as Easing },
  },
  slideRight: {
    initial: { opacity: 0, x: 20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -10 },
    transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] as Easing },
  },
  scale: {
    initial: { opacity: 0, scale: 0.96 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.98 },
    transition: { duration: 0.3, ease: "easeOut" as Easing },
  },
};

/**
 * Wraps page content with Framer Motion entrance animations.
 *
 * @example
 * ```tsx
 * <PageTransition variant="slideUp">
 *   <div className="page-shell">...</div>
 * </PageTransition>
 * ```
 */
export function PageTransition({
  variant = "slideUp",
  className,
  children,
  ...props
}: PageTransitionProps) {
  const v = variants[variant];

  return (
    <motion.div
      initial={v.initial}
      animate={v.animate}
      exit={v.exit}
      transition={v.transition}
      className={cn(className)}
      {...props}
    >
      {children}
    </motion.div>
  );
}

/**
 * Staggered container — children animate in sequence.
 *
 * @example
 * ```tsx
 * <StaggerContainer>
 *   <StaggerItem><Card>...</Card></StaggerItem>
 *   <StaggerItem><Card>...</Card></StaggerItem>
 * </StaggerContainer>
 * ```
 */
export function StaggerContainer({
  className,
  children,
  staggerDelay = 0.06,
  ...props
}: {
  className?: string;
  children: React.ReactNode;
  staggerDelay?: number;
} & HTMLMotionProps<"div">) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        hidden: {},
        visible: {
          transition: {
            staggerChildren: staggerDelay,
          },
        },
      }}
      className={cn(className)}
      {...props}
    >
      {children}
    </motion.div>
  );
}

export function StaggerItem({
  className,
  children,
  ...props
}: {
  className?: string;
  children: React.ReactNode;
} & HTMLMotionProps<"div">) {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 12 },
        visible: {
          opacity: 1,
          y: 0,
          transition: { duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] },
        },
      }}
      className={cn(className)}
      {...props}
    >
      {children}
    </motion.div>
  );
}
