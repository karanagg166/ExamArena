"use client";

import Link from "next/link";
import { useAuthStore } from "@/stores/useAuthStore";
import {
  GraduationCap,
  Building2,
  UserCircle,
  ArrowRight,
  Crown,
  School,
} from "lucide-react";
import { PageHeader } from "@/components/ui/page-header";
import { GlassCard } from "@/components/ui/glass-card";

export default function TeacherDashboard() {
  const { user } = useAuthStore();

  const links = [
    {
      title: "My Classes",
      description:
        "View your assigned classes, manage student rosters, and track progress.",
      href: "/teacher/classes",
      icon: GraduationCap,
      color: "text-[var(--info)]",
      bg: "bg-[var(--info-muted)]",
      hoverBg: "group-hover:bg-[var(--info)]",
    },
    {
      title: "School Directory",
      description:
        "Access information and contact details for your current school.",
      href: "/teacher/school",
      icon: Building2,
      color: "text-violet-400",
      bg: "bg-violet-500/15",
      hoverBg: "group-hover:bg-violet-500",
    },
    {
      title: "My Profile",
      description:
        "Update your subjects taught, qualifications, and contact info.",
      href: "/teacher/profile",
      icon: UserCircle,
      color: "text-[var(--warning)]",
      bg: "bg-[var(--warning-muted)]",
      hoverBg: "group-hover:bg-[var(--warning)]",
    },
    {
      title: "Become Principal",
      description:
        "Move to principal setup and choose to create a school or join one.",
      href: "/signup/principal",
      icon: Crown,
      color: "text-[var(--accent)]",
      bg: "bg-[var(--accent-muted)]",
      hoverBg: "group-hover:bg-[var(--accent)]",
    },
    {
      title: "Join a School",
      description:
        "Browse available schools and join directly from your teacher account.",
      href: "/teacher/school/join",
      icon: School,
      color: "text-[var(--success)]",
      bg: "bg-[var(--success-muted)]",
      hoverBg: "group-hover:bg-[var(--success)]",
    },
  ];

  return (
    <div className="page-shell">
      <div className="max-w-6xl mx-auto space-y-8 animate-fade-in-up">
        {/* Header Section */}
        <div className="glass-card p-8 md:p-12 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-600/10 via-transparent to-[var(--accent)]/5" />
          <div className="absolute top-0 right-0 p-12 opacity-[0.04] pointer-events-none">
            <GraduationCap size={200} />
          </div>
          <div className="relative z-10">
            <PageHeader
              overline="Teacher Dashboard"
              title={`Welcome back, ${user?.name?.split(" ")[0] || "Teacher"}!`}
              subtitle="Ready to inspire? Jump straight into your classes, view the school directory, or update your professional qualifications."
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
                className={`group block animate-fade-in-up stagger-${Math.min(i + 1, 6)}`}
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
