"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/axios";
import { Badge } from "@/components/ui/badge";
import { GlassCard } from "@/components/ui/glass-card";
import { PageHeader } from "@/components/ui/page-header";
import { Spinner } from "@/components/ui/loading";
import { Settings, UserCircle, ArrowRight } from "lucide-react";

type User = { name: string; role: string };

const ROLE_LINKS: Record<string, { label: string; href: string; description: string }> = {
  STUDENT: { label: "Student Profile", href: "/student", description: "Classes, exams, and school info" },
  TEACHER: { label: "Teacher Profile", href: "/teacher", description: "Classes, exams, and school directory" },
  PRINCIPAL: { label: "Principal Profile", href: "/principal", description: "School management and administration" },
};

const ROLE_COLORS: Record<string, string> = {
  STUDENT: "sky",
  TEACHER: "success",
  PRINCIPAL: "violet",
  ADMIN: "warning",
};

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/api/v1/auth/me")
      .then((r) => setUser(r.data))
      .catch(() => router.push("/login"))
      .finally(() => setLoading(false));
  }, [router]);

  if (loading)
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Spinner className="h-8 w-8 border-4" />
      </div>
    );

  const roleInfo = ROLE_LINKS[user?.role ?? ""];
  const roleColor = ROLE_COLORS[user?.role ?? ""] ?? "accent";

  const roleBadgeVariant = (() => {
    switch (user?.role) {
      case "STUDENT": return "default" as const;
      case "TEACHER": return "success" as const;
      case "PRINCIPAL": return "default" as const;
      case "ADMIN": return "warning" as const;
      default: return "neutral" as const;
    }
  })();

  return (
    <div className="page-shell">
      <div className="mx-auto max-w-4xl animate-fade-in-up">
        {/* Welcome header */}
        <div className="mb-10">
          <PageHeader
            overline="Welcome back"
            title={`${user?.name ?? "User"} 👋`}
            subtitle="Here's your quick access dashboard."
          />
          <Badge variant={roleBadgeVariant} className="mt-3 uppercase tracking-widest text-xs">
            {user?.role}
          </Badge>
        </div>

        {/* Quick Links */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <Link href="/profile" className="group block">
            <GlassCard interactive padding="md" className="h-full">
              <div className="flex items-start justify-between mb-4">
                <div className="rounded-xl bg-[var(--accent-muted)] p-2.5 text-[var(--accent)] transition-colors group-hover:bg-[var(--accent)] group-hover:text-white">
                  <Settings className="h-5 w-5" />
                </div>
                <ArrowRight className="h-4 w-4 text-[var(--text-dimmed)] group-hover:text-[var(--text-secondary)] transition-colors" />
              </div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1">
                Account Settings
              </h3>
              <p className="text-sm text-[var(--text-muted)]">
                Name, email, phone, address
              </p>
            </GlassCard>
          </Link>

          {roleInfo && (
            <Link href={roleInfo.href} className="group block">
              <GlassCard interactive padding="md" className="h-full">
                <div className="flex items-start justify-between mb-4">
                  <div className={`rounded-xl p-2.5 transition-colors ${
                    roleColor === "sky"
                      ? "bg-sky-500/15 text-sky-400 group-hover:bg-sky-500 group-hover:text-white"
                      : roleColor === "success"
                        ? "bg-[var(--success-muted)] text-[var(--success)] group-hover:bg-[var(--success)] group-hover:text-white"
                        : roleColor === "violet"
                          ? "bg-violet-500/15 text-violet-400 group-hover:bg-violet-500 group-hover:text-white"
                          : "bg-[var(--warning-muted)] text-[var(--warning)] group-hover:bg-[var(--warning)] group-hover:text-white"
                  }`}>
                    <UserCircle className="h-5 w-5" />
                  </div>
                  <ArrowRight className="h-4 w-4 text-[var(--text-dimmed)] group-hover:text-[var(--text-secondary)] transition-colors" />
                </div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1">
                  {roleInfo.label}
                </h3>
                <p className="text-sm text-[var(--text-muted)]">
                  {roleInfo.description}
                </p>
              </GlassCard>
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
