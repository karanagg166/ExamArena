import Link from "next/link";
import { ArrowRight, ShieldCheck, GraduationCap, Sparkles } from "lucide-react";
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
        <div className="rounded-3xl border border-zinc-800/80 bg-zinc-950/60 px-6 py-12 text-center shadow-2xl shadow-indigo-950/15 md:px-10 md:py-16">
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
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Button asChild size="lg">
              <Link href="/login">
                Login
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="secondary">
              <Link href="/signup">Create Account</Link>
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
