import Link from "next/link";
import {
  ArrowRight,
  ShieldCheck,
  GraduationCap,
  Sparkles,
  LogIn,
  UserPlus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";

const pillars = [
  {
    title: "Students",
    description:
      "Take exams, view results, and manage your class progress in one place.",
    icon: GraduationCap,
    color: "text-sky-400",
    bg: "bg-sky-500/15",
  },
  {
    title: "Teachers",
    description:
      "Create and review exams with cleaner workflows and structured data.",
    icon: Sparkles,
    color: "text-[var(--success)]",
    bg: "bg-[var(--success-muted)]",
  },
  {
    title: "Principals",
    description:
      "Organize school and class operations with role-aware controls.",
    icon: ShieldCheck,
    color: "text-[var(--accent)]",
    bg: "bg-[var(--accent-muted)]",
  },
];

export default function PublicLandingPage() {
  return (
    <main className="min-h-screen relative overflow-hidden flex flex-col">
      {/* Background animated gradient */}
      <div className="absolute inset-0 z-0 bg-gradient-to-br from-[var(--background)] via-[var(--surface-1)] to-[var(--background)]">
        <div className="absolute inset-0 animated-gradient opacity-30 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/40 via-transparent to-transparent" />
        <div
          className="absolute inset-0 animated-gradient opacity-20 bg-[radial-gradient(ellipse_at_bottom_left,_var(--tw-gradient-stops))] from-emerald-900/30 via-transparent to-transparent"
          style={{ animationDelay: "-3s" }}
        />
      </div>

      {/* Navbar */}
      <nav className="glass-nav sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--accent)] text-white font-bold text-sm">
            EA
          </div>
          <span className="font-bold text-[var(--text-primary)] text-lg tracking-tight">
            Exam Arena
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
            <Link href="/login">Log in</Link>
          </Button>
          <Button asChild variant="primary" size="sm" className="rounded-full px-5">
            <Link href="/signup">Sign up free</Link>
          </Button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative z-10 flex-1 flex flex-col items-center justify-center px-4 py-20 text-center animate-fade-in-up">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[var(--border-subtle)] bg-[var(--surface-2)] text-xs font-semibold text-[var(--accent)] mb-8">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--accent)] opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--accent)]" />
          </span>
          A focused exam platform for every academic role
        </div>

        <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-[var(--text-primary)] max-w-4xl mb-6">
          The modern platform for <br className="hidden md:block" />
          <span className="text-gradient">digital assessments.</span>
        </h1>

        <p className="text-lg md:text-xl text-[var(--text-secondary)] max-w-2xl mb-10 leading-relaxed">
          Unified workflows for students, teachers, and principals with secure
          auth and role-based pages.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
          <Button asChild size="lg" className="rounded-full px-8 text-base">
            <Link href="/signup">
              <UserPlus className="h-5 w-5 mr-2" /> Get Started
            </Link>
          </Button>
          <Button
            asChild
            size="lg"
            variant="secondary"
            className="rounded-full px-8 text-base bg-white/5 border border-white/10 hover:bg-white/10"
          >
            <Link href="/login">
              <LogIn className="h-5 w-5 mr-2" /> Sign In
            </Link>
          </Button>
        </div>
      </section>

      {/* Role Cards */}
      <section className="relative z-10 max-w-6xl mx-auto px-4 pb-24 w-full grid grid-cols-1 md:grid-cols-3 gap-6">
        {pillars.map((pillar, i) => {
          const Icon = pillar.icon;
          return (
            <GlassCard
              key={pillar.title}
              interactive
              padding="lg"
              className={`animate-fade-in-up stagger-${i + 1} group`}
            >
              <div
                className={`h-12 w-12 rounded-2xl ${pillar.bg} ${pillar.color} flex items-center justify-center mb-6 transition-transform group-hover:scale-110 group-hover:rotate-3 duration-300`}
              >
                <Icon className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-semibold text-[var(--text-primary)] mb-3">
                {pillar.title}
              </h3>
              <p className="text-[var(--text-secondary)] text-sm leading-relaxed">
                {pillar.description}
              </p>
              <div className="mt-6">
                <Link
                  href="/signup"
                  className="inline-flex items-center gap-1.5 text-sm font-medium text-[var(--accent)] hover:text-[var(--accent-hover)] transition-colors"
                >
                  Get started <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </GlassCard>
          );
        })}
      </section>
    </main>
  );
}
