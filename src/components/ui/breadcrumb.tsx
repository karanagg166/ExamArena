"use client";

import * as React from "react";
import Link from "next/link";
import { ChevronRight, Home } from "lucide-react";
import { cn } from "@/lib/utils";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  /** Show home icon as first item */
  showHome?: boolean;
  className?: string;
}

export function Breadcrumb({
  items,
  showHome = true,
  className,
}: BreadcrumbProps) {
  return (
    <nav
      aria-label="Breadcrumb"
      className={cn("flex items-center gap-1.5 text-sm", className)}
    >
      {showHome && (
        <>
          <Link
            href="/"
            className="text-[var(--text-muted)] transition-colors hover:text-[var(--text-primary)]"
          >
            <Home className="h-3.5 w-3.5" />
          </Link>
          {items.length > 0 && (
            <ChevronRight className="h-3.5 w-3.5 text-[var(--text-dimmed)]" />
          )}
        </>
      )}
      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        return (
          <React.Fragment key={item.label}>
            {isLast || !item.href ? (
              <span
                className={cn(
                  isLast
                    ? "font-medium text-[var(--text-primary)]"
                    : "text-[var(--text-muted)]",
                )}
              >
                {item.label}
              </span>
            ) : (
              <Link
                href={item.href}
                className="text-[var(--text-muted)] transition-colors hover:text-[var(--text-primary)]"
              >
                {item.label}
              </Link>
            )}
            {!isLast && (
              <ChevronRight className="h-3.5 w-3.5 text-[var(--text-dimmed)]" />
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}
