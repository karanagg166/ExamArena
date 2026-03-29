"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogIn, UserPlus, LogOut } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/useAuthStore";

export default function HomePage() {
  const router = useRouter();
  const logout = useAuthStore((state) => state.logout);
  const user = useAuthStore((state) => state.user);
  const loading = useAuthStore((state) => state.loading);

  const handleLogout = async () => {
    await logout();
    router.push("/");
    router.refresh();
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-zinc-950 via-slate-950 to-zinc-900 px-6 py-16 text-white">
      <section className="mx-auto max-w-5xl">
        <div className="rounded-3xl border border-zinc-800/80 bg-zinc-900/50 p-8 shadow-2xl backdrop-blur md:p-12">
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.24em] text-emerald-300">
            Exam Arena
          </p>
          <h1 className="text-3xl font-bold tracking-tight md:text-5xl">
            Welcome to the platform
          </h1>
          <p className="mt-4 max-w-2xl text-sm text-zinc-300 md:text-base">
            Use quick actions below to login, create an account, or logout from
            your current session.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg" className="rounded-xl px-6">
              <Link href="/login">
                <LogIn className="h-4 w-4" />
                Login
              </Link>
            </Button>

            <Button
              asChild
              size="lg"
              variant="secondary"
              className="rounded-xl px-6"
            >
              <Link href="/signup">
                <UserPlus className="h-4 w-4" />
                Sign Up
              </Link>
            </Button>

            <Button
              type="button"
              size="lg"
              variant="outline"
              className="rounded-xl border-red-400/40 bg-red-500/10 px-6 text-red-200 hover:bg-red-500/20"
              onClick={handleLogout}
              disabled={loading}
            >
              <LogOut className="h-4 w-4" />
              {loading ? "Logging Out..." : "Logout"}
            </Button>
          </div>

          {user && (
            <p className="mt-5 text-sm text-zinc-300">
              Logged in as{" "}
              <span className="font-semibold text-white">{user.name}</span>
            </p>
          )}
        </div>
      </section>
    </main>
  );
}
