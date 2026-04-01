"use client";

import Link from "next/link";
import { useAuthStore } from "@/stores/useAuthStore";
import { School, Users, UserCircle, ArrowRight } from "lucide-react";
import { PageHeader } from "@/components/ui/page-header";
import { GlassCard } from "@/components/ui/glass-card";

export default function PrincipalDashboard() {
  const { user } = useAuthStore();

  const links = [
    {
      title: "School Profile",
      description:
        "Manage your school's core details and administration settings.",
      href: "/principal/school",
      icon: School,
      color: "text-[var(--accent)]",
      bg: "bg-[var(--accent-muted)]",
      hoverBg: "group-hover:bg-[var(--accent)]",
    },
    {
      title: "Classes & Staff",
      description:
        "Oversee all classes, student rosters, and assigned teachers.",
      href: "/principal/school/classes",
      icon: Users,
      color: "text-[var(--success)]",
      bg: "bg-[var(--success-muted)]",
      hoverBg: "group-hover:bg-[var(--success)]",
    },
    {
      title: "My Profile",
      description:
        "Update your personal credentials and professional experience.",
      href: "/principal/profile",
      icon: UserCircle,
      color: "text-[var(--warning)]",
      bg: "bg-[var(--warning-muted)]",
      hoverBg: "group-hover:bg-[var(--warning)]",
    },
  ];

  return (
    <div className="page-shell">
      <div className="max-w-6xl mx-auto space-y-8 animate-fade-in-up">
        {/* Header Section */}
        <div className="glass-card p-8 md:p-12 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-violet-600/10 via-transparent to-[var(--accent)]/5" />
          <div className="absolute top-0 right-0 p-12 opacity-[0.04] pointer-events-none">
            <School size={200} />
          </div>
          <div className="relative z-10">
            <PageHeader
              overline="Principal Dashboard"
              title={`Welcome back, ${user?.name?.split(" ")[0] || "Principal"}!`}
              subtitle="Access your school's command center. From here, you can manage your school's infrastructure, oversee all classes, and keep your profile up to date."
            />
          </div>
        </div>

        {/* Quick Links Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {links.map((link, i) => {
            const Icon = link.icon;
            return (
              <Link
                key={link.title}
                href={link.href}
                className={`group block animate-fade-in-up stagger-${i + 1}`}
              >
                <GlassCard interactive padding="md" className="h-full">
                  <div className="flex items-center justify-between mb-4">
                    <div
                      className={`p-3 rounded-xl ${link.bg} ${link.color} ${link.hoverBg} group-hover:text-white transition-colors`}
                    >
                      <Icon size={22} />
                    </div>
                    <ArrowRight className="w-4 h-4 text-[var(--text-dimmed)] group-hover:text-[var(--text-secondary)] transition-colors" />
                  </div>
                  <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1.5">
                    {link.title}
                  </h3>
                  <p className="text-sm text-[var(--text-muted)] leading-relaxed">
                    {link.description}
                  </p>
                </GlassCard>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
