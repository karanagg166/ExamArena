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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const pillars = [
  {
    title: "Students",
    description:
      "Take exams, view results, and manage your class progress in one place.",
    icon: GraduationCap,
  },
  {
    title: "Teachers",
    description:
      "Create and review exams with cleaner workflows and structured data.",
    icon: Sparkles,
  },
  {
    title: "Principals",
    description:
      "Organize school and class operations with role-aware controls.",
    icon: ShieldCheck,
  },
];

export default function PublicLandingPage() {
  return (
    <main className="page-shell text-white">
      <section className="mx-auto max-w-5xl">
        <div className="relative overflow-hidden rounded-3xl border border-zinc-800/80 bg-zinc-950/60 px-6 py-12 text-center shadow-2xl shadow-indigo-950/15 md:px-10 md:py-16">
          <div className="pointer-events-none absolute left-0 top-0 h-36 w-36 -translate-x-1/3 -translate-y-1/3 rounded-full bg-indigo-500/25 blur-3xl" />
          <div className="pointer-events-none absolute bottom-0 right-0 h-40 w-40 translate-x-1/4 translate-y-1/4 rounded-full bg-emerald-500/20 blur-3xl" />

          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.24em] text-indigo-300">
            Exam Arena
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-zinc-100 md:text-5xl">
            A focused exam platform for every academic role
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-sm text-zinc-400 md:text-base">
            Unified workflows for students, teachers, and principals with secure
            auth and role-based pages.
          </p>
          <div className="mt-9 flex flex-wrap items-center justify-center gap-4">
            <Button
              asChild
              size="lg"
              className="h-12 min-w-40 rounded-2xl bg-gradient-to-r from-indigo-500 to-blue-500 text-base font-bold text-white shadow-lg shadow-indigo-600/30 hover:from-indigo-400 hover:to-blue-400"
            >
              <Link href="/login">
                <LogIn className="h-4 w-4" />
                Login
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>

            <Button
              asChild
              size="lg"
              variant="outline"
              className="h-12 min-w-40 rounded-2xl border-emerald-400/35 bg-emerald-500/10 text-base font-bold text-emerald-200 shadow-md shadow-emerald-700/10 hover:bg-emerald-500/20"
            >
              <Link href="/signup">
                <UserPlus className="h-4 w-4" />
                Sign Up
              </Link>
            </Button>
          </div>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {pillars.map((pillar) => {
            const Icon = pillar.icon;
            return (
              <Card key={pillar.title}>
                <CardHeader>
                  <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-xl border border-zinc-700 bg-zinc-900">
                    <Icon className="h-5 w-5 text-indigo-300" />
                  </div>
                  <CardTitle>{pillar.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-zinc-400">{pillar.description}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>
    </main>
  );
}
