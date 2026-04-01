"use client";

import Link from "next/link";
import { useAuthStore } from "@/stores/useAuthStore";
import { Users, Library, UserCircle, ArrowRight } from "lucide-react";
import { PageHeader } from "@/components/ui/page-header";
import { GlassCard } from "@/components/ui/glass-card";

export default function StudentDashboard() {
  const { user } = useAuthStore();

  const links = [
    {
      title: "My Class",
      description:
        "Check out your classmates, class details, and assigned teachers.",
      href: "/student/class",
      icon: Users,
      color: "text-[var(--success)]",
      bg: "bg-[var(--success-muted)]",
      hoverBg: "group-hover:bg-[var(--success)]",
    },
    {
      title: "School Facts",
      description: "Learn more about your school's administration and details.",
      href: "/student/school",
      icon: Library,
      color: "text-violet-400",
      bg: "bg-violet-500/15",
      hoverBg: "group-hover:bg-violet-500",
    },
    {
      title: "My Details",
      description:
        "Keep your personal information and student profile up to date.",
      href: "/student/profile",
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
          <div className="absolute inset-0 bg-gradient-to-br from-sky-600/10 via-transparent to-[var(--accent)]/5" />
          <div className="absolute top-0 right-0 p-12 opacity-[0.04] pointer-events-none">
            <Users size={200} />
          </div>
          <div className="relative z-10">
            <PageHeader
              overline="Student Dashboard"
              title={`Welcome back, ${user?.name?.split(" ")[0] || "Student"}!`}
              subtitle="Your student hub is ready. Dive into your class details, view school information, or manage your profile."
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
