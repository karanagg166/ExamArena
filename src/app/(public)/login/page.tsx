"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  LogIn,
  Mail,
  Lock,
  ArrowRight,
  ShieldCheck,
  GraduationCap,
  Sparkles,
  Eye,
  EyeOff,
} from "lucide-react";
import Link from "next/link";
import axios from "axios";
import { api } from "@/lib/axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FormMessage } from "@/components/ui/form-message";
import { Spinner } from "@/components/ui/loading";

const features = [
  { icon: ShieldCheck, text: "Secure role-based access" },
  { icon: GraduationCap, text: "Personalized dashboards" },
  { icon: Sparkles, text: "Real-time exam management" },
];

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
      const response = await api.post("/api/v1/auth/login", { email, password });

      if (response.status === 200) {
        const user = response.data;
        switch (user.role.toLowerCase()) {
          case "student":    router.push("/student");       break;
          case "teacher":    router.push("/teacher");       break;
          case "principal":  router.push("/principal");     break;
          case "admin":      router.push("/admin/profile"); break;
          default:           router.push("/");
        }
      } else {
        setError("Invalid credentials. Please try again.");
      }
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || "Invalid credentials. Please try again.");
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
    <div className="flex min-h-screen bg-background">
      {/* ─── Left brand panel ─── */}
      <motion.div
        initial={{ opacity: 0, x: -24 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="hidden lg:flex lg:w-1/2 flex-col justify-between bg-indigo-600 px-14 py-12 text-white"
      >
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/20 text-sm font-bold backdrop-blur-sm">
            EA
          </div>
          <span className="font-semibold text-lg tracking-tight">Exam Arena</span>
        </Link>

        {/* Headline */}
        <div className="max-w-sm">
          <h2 className="text-4xl font-bold tracking-tight leading-tight mb-4">
            Welcome back to your academic hub.
          </h2>
          <p className="text-indigo-100 text-base leading-relaxed mb-10">
            Sign in to manage exams, track progress, and stay connected with your school.
          </p>

          <div className="space-y-4">
            {features.map((item) => (
              <div key={item.text} className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/15">
                  <item.icon className="h-4 w-4" />
                </div>
                <span className="text-sm text-indigo-100">{item.text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer text */}
        <p className="text-xs text-indigo-200">
          © {new Date().getFullYear()} Exam Arena · Secure · Reliable
        </p>
      </motion.div>

      {/* ─── Right form panel ─── */}
      <div className="flex w-full lg:w-1/2 items-center justify-center px-4 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
          className="w-full max-w-md"
        >
          {/* Mobile logo */}
          <Link href="/" className="flex items-center gap-2.5 mb-8 lg:hidden">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white text-xs font-bold">
              EA
            </div>
            <span className="font-semibold text-foreground">Exam Arena</span>
          </Link>

          {/* Form header */}
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-foreground tracking-tight">Sign in</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Enter your credentials to access your account
            </p>
          </div>

          <FormMessage message={error} type="error" className="mb-5" />

          <form onSubmit={handleLogin} className="space-y-5">
            {/* Email */}
            <div className="space-y-1.5">
              <Label htmlFor="email">Email Address</Label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none" />
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

            {/* Password */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <Link
                  href="/forgot-password"
                  className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline transition-colors"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none" />
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
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Submit */}
            <Button
              type="submit"
              disabled={loading}
              className="mt-2 h-11 w-full bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm"
            >
              {loading ? (
                <Spinner className="h-4 w-4 border-white/40 border-t-white" />
              ) : (
                <>
                  Sign In <ArrowRight className="h-4 w-4 ml-1" />
                </>
              )}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">or</span>
            </div>
          </div>

          <p className="text-center text-sm text-muted-foreground">
            Don&apos;t have an account?{" "}
            <Link
              href="/signup"
              className="font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              Sign up free
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default LoginPage;
