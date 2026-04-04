"use client";

import Link from "next/link";
import { LogIn, UserPlus, GraduationCap, School, ChevronRight, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/useAuthStore";
import { GlassCard } from "@/components/ui/glass-card";

export default function HomePage() {
  const user = useAuthStore((state) => state.user);

  return (
    <main className="min-h-screen relative overflow-hidden flex flex-col">
      {/* Background animated gradient */}
      <div className="absolute inset-0 z-0 bg-gradient-to-br from-[#09090b] via-[#111114] to-[#09090b]">
        <div className="absolute inset-0 animated-gradient opacity-30 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/40 via-transparent to-transparent" />
        <div className="absolute inset-0 animated-gradient opacity-20 bg-[radial-gradient(ellipse_at_bottom_left,_var(--tw-gradient-stops))] from-emerald-900/30 via-transparent to-transparent" style={{ animationDelay: "-3s" }} />
      </div>

      {/* Navbar (Public) */}
      <nav className="glass-nav sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--accent)] text-white font-bold">
            EA
          </div>
          <span className="font-bold text-[var(--text-primary)] text-lg tracking-tight">Exam Arena</span>
        </div>
        <div className="flex items-center gap-3">
          {user ? (
            <Button asChild variant="primary" size="sm" className="rounded-full px-5">
              <Link href="/dashboard">
                Go to Dashboard <ChevronRight className="h-4 w-4 ml-1" />
              </Link>
            </Button>
          ) : (
            <>
              <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
                <Link href="/login">Log in</Link>
              </Button>
              <Button asChild variant="primary" size="sm" className="rounded-full px-5">
                <Link href="/signup">Sign up free</Link>
              </Button>
            </>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative z-10 flex-1 flex flex-col items-center justify-center px-4 py-20 text-center animate-fade-in-up">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[var(--border-subtle)] bg-[var(--surface-2)] text-xs font-semibold text-[var(--accent)] mb-8">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--accent)] opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--accent)]"></span>
          </span>
          Exam Arena 2.0 is live
        </div>
        
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-[var(--text-primary)] max-w-4xl mb-6">
          The modern platform for <br className="hidden md:block" />
          <span className="text-gradient">digital assessments.</span>
        </h1>
        
        <p className="text-lg md:text-xl text-[var(--text-secondary)] max-w-2xl mb-10 leading-relaxed">
          A role-based examination ecosystem built for principals, teachers, and students. Create, administer, and analyze tests with zero friction.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
          {!user && (
            <>
              <Button asChild size="lg" className="rounded-full px-8 text-base">
                <Link href="/signup">
                  <UserPlus className="h-5 w-5 mr-2" /> Get Started
                </Link>
              </Button>
              <Button asChild size="lg" variant="secondary" className="rounded-full px-8 text-base bg-white/5 border border-white/10 hover:bg-white/10">
                <Link href="/login">
                  <LogIn className="h-5 w-5 mr-2" /> Sign In
                </Link>
              </Button>
            </>
          )}
        </div>
      </section>

      {/* Role Cards Section */}
      <section className="relative z-10 max-w-6xl mx-auto px-4 pb-24 w-full grid grid-cols-1 md:grid-cols-3 gap-6">
        <GlassCard interactive padding="lg" className="animate-fade-in-up stagger-1 group">
          <div className="h-12 w-12 rounded-2xl bg-[var(--accent-muted)] text-[var(--accent)] flex items-center justify-center mb-6 transition-transform group-hover:scale-110 group-hover:rotate-3 duration-300">
            <School className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-semibold text-[var(--text-primary)] mb-3">For Principals</h3>
          <p className="text-[var(--text-secondary)] text-sm mb-6 leading-relaxed">
            Register your school, manage teacher approvals, and oversee the entire academic ecosystem from a unified dashboard.
          </p>
          <ul className="space-y-2 text-sm text-[var(--text-muted)]">
            <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-[var(--success)]" /> Centralized management</li>
            <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-[var(--success)]" /> Role-based access control</li>
          </ul>
        </GlassCard>

        <GlassCard interactive padding="lg" className="animate-fade-in-up stagger-2 group relative top-0 md:top-8">
          <div className="h-12 w-12 rounded-2xl bg-[var(--success-muted)] text-[var(--success)] flex items-center justify-center mb-6 transition-transform group-hover:scale-110 group-hover:-rotate-3 duration-300">
            <GraduationCap className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-semibold text-[var(--text-primary)] mb-3">For Teachers</h3>
          <p className="text-[var(--text-secondary)] text-sm mb-6 leading-relaxed">
            Craft rich assessments, organize classes, and grade instantly. Say goodbye to manual paper grading and administrative overhead.
          </p>
          <ul className="space-y-2 text-sm text-[var(--text-muted)]">
            <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-[var(--success)]" /> Advanced exam builder</li>
            <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-[var(--success)]" /> Automated grading</li>
          </ul>
        </GlassCard>

        <GlassCard interactive padding="lg" className="animate-fade-in-up stagger-3 group">
          <div className="h-12 w-12 rounded-2xl bg-sky-500/15 text-sky-400 flex items-center justify-center mb-6 transition-transform group-hover:scale-110 group-hover:rotate-3 duration-300">
            <UserPlus className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-semibold text-[var(--text-primary)] mb-3">For Students</h3>
          <p className="text-[var(--text-secondary)] text-sm mb-6 leading-relaxed">
            Take exams in a distraction-free, high-performance environment. Track progress, view results instantly, and focus on learning.
          </p>
          <ul className="space-y-2 text-sm text-[var(--text-muted)]">
            <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-[var(--success)]" /> Distraction-free testing</li>
            <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-[var(--success)]" /> Instant performance insights</li>
          </ul>
        </GlassCard>
      </section>
    </main>
  );
}
