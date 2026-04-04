"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { LogIn, Mail, Lock, ArrowRight, ShieldCheck, GraduationCap, Sparkles, Eye, EyeOff } from "lucide-react";
import Link from "next/link";
import axios from "axios";
import { api } from "@/lib/axios";
import { Button } from "@/components/ui/button";
import { FormMessage } from "@/components/ui/form-message";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/loading";
import { GlassCard } from "@/components/ui/glass-card";

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await api.post("/api/v1/auth/login", {
        email,
        password,
      });

      if (response.status === 200) {
        const user = response.data;

        switch (user.role.toLowerCase()) {
          case "student":
            router.push("/student");
            break;
          case "teacher":
            router.push("/teacher");
            break;
          case "principal":
            router.push("/principal");
            break;
          case "admin":
            router.push("/admin/profile");
            break;
          default:
            router.push("/");
        }
      } else {
        setError("Invalid credentials. Please try again.");
      }
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(
          err.response?.data?.detail ||
            "Invalid credentials. Please try again.",
        );
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An error occurred. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 z-0 bg-[var(--background)]">
        <div className="absolute inset-0 animated-gradient opacity-30 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/40 via-transparent to-transparent" />
        <div
          className="absolute inset-0 animated-gradient opacity-20 bg-[radial-gradient(ellipse_at_bottom_left,_var(--tw-gradient-stops))] from-emerald-900/30 via-transparent to-transparent"
          style={{ animationDelay: "-3s" }}
        />
      </div>

      {/* Left panel — Brand (hidden on mobile) */}
      <div className="hidden lg:flex lg:w-1/2 relative z-10 flex-col justify-center px-16">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-md"
        >
          <div className="flex items-center gap-3 mb-10">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--accent)] text-white font-bold">
              EA
            </div>
            <span className="font-bold text-[var(--text-primary)] text-xl tracking-tight">
              Exam Arena
            </span>
          </div>

          <h2 className="text-4xl font-bold text-[var(--text-primary)] tracking-tight mb-4">
            Welcome back to your{" "}
            <span className="text-gradient">academic hub.</span>
          </h2>
          <p className="text-[var(--text-secondary)] text-lg leading-relaxed mb-10">
            Sign in to manage exams, track progress, and stay connected with
            your school.
          </p>

          <div className="space-y-4">
            {[
              { icon: ShieldCheck, text: "Secure role-based access" },
              { icon: GraduationCap, text: "Personalized dashboards" },
              { icon: Sparkles, text: "Real-time exam management" },
            ].map((item) => (
              <div key={item.text} className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--accent-muted)]">
                  <item.icon className="h-4 w-4 text-[var(--accent)]" />
                </div>
                <span className="text-sm text-[var(--text-secondary)]">
                  {item.text}
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Right panel — Form */}
      <div className="flex w-full lg:w-1/2 items-center justify-center px-4 py-12 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="w-full max-w-md"
        >
          <GlassCard padding="lg" className="shadow-2xl shadow-indigo-900/10">
            {/* Header */}
            <div className="text-center mb-8">
              <div className="mb-4 flex justify-center lg:hidden">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--accent-muted)] border border-[var(--accent)]/20">
                  <LogIn className="h-7 w-7 text-[var(--accent)]" />
                </div>
              </div>
              <div className="hidden lg:flex mb-4 justify-center">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--accent-muted)] border border-[var(--accent)]/20">
                  <LogIn className="h-7 w-7 text-[var(--accent)]" />
                </div>
              </div>
              <h1 className="text-2xl font-bold text-[var(--text-primary)]">
                Sign in
              </h1>
              <p className="text-sm text-[var(--text-muted)] mt-1">
                Enter your credentials to access your account
              </p>
            </div>

            <FormMessage
              message={error}
              type="error"
              className="mb-5 text-center"
            />

            <form onSubmit={handleLogin} className="space-y-5">
              <div className="space-y-1.5">
                <Label htmlFor="email">Email Address</Label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-dimmed)]" />
                  <Input
                    type="email"
                    id="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="h-11 pl-11"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password">Password</Label>
                  <Link
                    href="/forgot-password"
                    className="text-xs text-[var(--accent)] transition-colors hover:text-[var(--accent-hover)]"
                  >
                    Forgot password?
                  </Link>
                </div>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-dimmed)]" />
                  <Input
                    type={showPassword ? "text" : "password"}
                    id="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="h-11 pl-11 pr-11"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[var(--text-dimmed)] hover:text-[var(--text-primary)] transition-colors"
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="mt-2 h-11 w-full"
              >
                {loading ? (
                  <Spinner className="h-4 w-4 border-white/40 border-t-white" />
                ) : (
                  <>
                    Sign In
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </Button>
            </form>

            <p className="mt-7 text-center text-sm text-[var(--text-muted)]">
              Don&apos;t have an account yet?{" "}
              <Link
                href="/signup"
                className="font-medium text-[var(--accent)] transition-colors hover:text-[var(--accent-hover)]"
              >
                Sign up now
              </Link>
            </p>
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
};

export default LoginPage;
