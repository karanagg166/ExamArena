"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  LogIn,
  UserPlus,
  GraduationCap,
  School,
  ChevronRight,
  CheckCircle2,
  Sun,
  Moon,
} from "lucide-react";
import { useTheme } from "next-themes";
import React from "react";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/useAuthStore";

import type { Variants } from "framer-motion";

/* ─── Animation variants ─── */
const fadeUp: Variants = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] },
  },
};

const stagger: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
};

/* ─── Role card data ─── */
const roles = [
  {
    icon: School,
    title: "For Principals",
    description:
      "Register your school, manage teacher approvals, and oversee the entire academic ecosystem from a unified dashboard.",
    features: ["Centralized management", "Role-based access control"],
    accent: "bg-violet-50 dark:bg-violet-950/30 text-violet-600 dark:text-violet-400",
    iconBg: "bg-violet-100 dark:bg-violet-900/40",
    border: "hover:border-violet-200 dark:hover:border-violet-800",
  },
  {
    icon: GraduationCap,
    title: "For Teachers",
    description:
      "Craft rich assessments, organize classes, and grade instantly. Say goodbye to manual paper grading.",
    features: ["Advanced exam builder", "Automated grading"],
    accent: "bg-emerald-50 dark:bg-emerald-950/30 text-emerald-600 dark:text-emerald-400",
    iconBg: "bg-emerald-100 dark:bg-emerald-900/40",
    border: "hover:border-emerald-200 dark:hover:border-emerald-800",
    featured: true,
  },
  {
    icon: UserPlus,
    title: "For Students",
    description:
      "Take exams in a distraction-free, high-performance environment. Track progress and view results instantly.",
    features: ["Distraction-free testing", "Instant performance insights"],
    accent: "bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400",
    iconBg: "bg-blue-100 dark:bg-blue-900/40",
    border: "hover:border-blue-200 dark:hover:border-blue-800",
  },
];

export default function HomePage() {
  const user = useAuthStore((state) => state.user);
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => setMounted(true), []);

  return (
    <main className="min-h-screen flex flex-col bg-background">
      {/* ─── Navbar ─── */}
      <nav className="sticky top-0 z-50 glass-nav px-5 py-3.5 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white text-xs font-bold shadow-sm group-hover:shadow-indigo-300/50 transition-shadow duration-300">
            EA
          </div>
          <span className="font-semibold text-foreground tracking-tight">Exam Arena</span>
        </Link>

        <div className="flex items-center gap-2">
          {/* Theme toggle */}
          {mounted && (
            <button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="h-8 w-8 flex items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
          )}

          {user ? (
            <Button asChild size="sm" className="rounded-full px-5 bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm">
              <Link href="/dashboard">
                Dashboard <ChevronRight className="h-4 w-4 ml-1" />
              </Link>
            </Button>
          ) : (
            <>
              <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
                <Link href="/login">Log in</Link>
              </Button>
              <Button asChild size="sm" className="rounded-full px-5 bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm">
                <Link href="/signup">Sign up free</Link>
              </Button>
            </>
          )}
        </div>
      </nav>

      {/* ─── Hero ─── */}
      <motion.section
        className="flex flex-col items-center justify-center px-4 py-24 text-center flex-1"
        variants={stagger}
        initial="hidden"
        animate="show"
      >
        {/* Live badge */}
        <motion.div
          variants={fadeUp}
          custom={0}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-card text-xs font-semibold text-indigo-600 dark:text-indigo-400 mb-8 shadow-sm"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-500 opacity-60" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500" />
          </span>
          Exam Arena 2.0 — Now Live
        </motion.div>

        {/* Headline */}
        <motion.h1
          variants={fadeUp}
          custom={1}
          className="text-5xl md:text-7xl font-bold tracking-tight text-foreground max-w-4xl mb-6 leading-tight"
        >
          The modern platform for{" "}
          <br className="hidden md:block" />
          <span className="text-gradient">digital assessments.</span>
        </motion.h1>

        {/* Subtext */}
        <motion.p
          variants={fadeUp}
          custom={2}
          className="text-lg md:text-xl text-muted-foreground max-w-2xl mb-10 leading-relaxed"
        >
          A role-based examination ecosystem built for principals, teachers, and students.
          Create, administer, and analyze tests with zero friction.
        </motion.p>

        {/* CTAs */}
        {!user && (
          <motion.div
            variants={fadeUp}
            custom={3}
            className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto"
          >
            <Button
              asChild
              size="lg"
              className="rounded-full px-8 text-base bg-indigo-600 hover:bg-indigo-700 text-white shadow-md hover:shadow-indigo-200/60 dark:hover:shadow-indigo-900/40 transition-all"
            >
              <Link href="/signup">
                <UserPlus className="h-5 w-5 mr-2" /> Get Started Free
              </Link>
            </Button>
            <Button
              asChild
              size="lg"
              variant="outline"
              className="rounded-full px-8 text-base border-border hover:bg-accent"
            >
              <Link href="/login">
                <LogIn className="h-5 w-5 mr-2" /> Sign In
              </Link>
            </Button>
          </motion.div>
        )}
      </motion.section>

      {/* ─── Role Cards ─── */}
      <motion.section
        className="max-w-6xl mx-auto px-4 pb-28 w-full grid grid-cols-1 md:grid-cols-3 gap-5 items-start"
        variants={stagger}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, amount: 0.2 }}
      >
        {roles.map((role, i) => (
          <motion.div
            key={role.title}
            variants={fadeUp}
            custom={i}
            whileHover={{ y: -4, transition: { duration: 0.2 } }}
            className={`relative rounded-2xl border border-border bg-card p-6 shadow-sm transition-all duration-300 ${role.border} ${role.featured ? "md:scale-[1.02] shadow-md" : ""}`}
          >
            {role.featured && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <span className="bg-indigo-600 text-white text-xs font-semibold px-3 py-1 rounded-full shadow-sm">
                  Most Popular
                </span>
              </div>
            )}

            {/* Icon */}
            <div className={`h-11 w-11 rounded-xl ${role.iconBg} ${role.accent} flex items-center justify-center mb-5 transition-transform group-hover:scale-110 duration-300`}>
              <role.icon className="h-5 w-5" />
            </div>

            <h3 className="text-lg font-semibold text-foreground mb-2">{role.title}</h3>
            <p className="text-sm text-muted-foreground mb-5 leading-relaxed">{role.description}</p>

            <ul className="space-y-2">
              {role.features.map((f) => (
                <li key={f} className="flex items-center gap-2 text-sm text-muted-foreground">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
          </motion.div>
        ))}
      </motion.section>

      {/* ─── Footer ─── */}
      <footer className="border-t border-border bg-card/50 py-6 text-center text-xs text-muted-foreground">
        © {new Date().getFullYear()} Exam Arena. Built with ❤️ for modern education.
      </footer>
    </main>
  );
}
