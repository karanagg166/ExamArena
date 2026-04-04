"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import axios from "axios";
import { api } from "@/lib/axios";
import { SignUpForm } from "@/types/user";
import { useAuthStore } from "@/stores";
import { toast } from "sonner";
import { UserPlus, Eye, EyeOff, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { FormMessage } from "@/components/ui/form-message";
import { GlassCard } from "@/components/ui/glass-card";
import { Spinner } from "@/components/ui/loading";

type ValidationError = {
  msg: string;
};

const SignUpPage = () => {
  const router = useRouter();
  const { login } = useAuthStore();
  const [form, setForm] = useState<SignUpForm>({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    phoneNo: "",
    dateOfBirth: "",
    role: "STUDENT",
    pincode: "",
    city: "",
    state: "",
    country: "",
  });

  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const onSubmit = async () => {
    if (loading) return;

    const { name, email, password, confirmPassword } = form;

    if (!name || !email || !password) {
      const message = "Please fill all required fields";
      setError(message);
      toast.error(message);
      return;
    }

    if (password.length < 6) {
      const message = "Password must be at least 6 characters";
      setError(message);
      toast.error(message);
      return;
    }

    if (password !== confirmPassword) {
      const message = "Passwords do not match";
      setError(message);
      toast.error(message);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const { confirmPassword, ...payload } = form;
      void confirmPassword;

      const data = await api.post("/api/v1/auth/signup", payload);
      console.log("Signup response:", data);

      setSuccess(true);
      toast.success("Account created successfully");
      login(form.email, form.password);
      console.log("Logged in user after signup:", form.role.toLowerCase());
      router.push(`/signup/${form.role.toLowerCase()}`);
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        if (Array.isArray(detail)) {
          const messages = detail
            .filter(
              (item): item is ValidationError =>
                typeof item === "object" &&
                item !== null &&
                "msg" in item &&
                typeof (item as { msg?: unknown }).msg === "string",
            )
            .map((errObj) => errObj.msg);
          const message = messages.length
            ? messages.join(", ")
            : "Validation failed";
          setError(message);
          toast.error(message);
        } else if (typeof detail === "string") {
          setError(detail);
          toast.error(detail);
        } else {
          const message = "Something went wrong during signup.";
          setError(message);
          toast.error(message);
        }
      } else {
        const message = "Unexpected error occurred";
        setError(message);
        toast.error(message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 z-0 bg-[var(--background)]">
        <div className="absolute inset-0 animated-gradient opacity-30 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/40 via-transparent to-transparent" />
        <div
          className="absolute inset-0 animated-gradient opacity-20 bg-[radial-gradient(ellipse_at_bottom_left,_var(--tw-gradient-stops))] from-emerald-900/30 via-transparent to-transparent"
          style={{ animationDelay: "-3s" }}
        />
      </div>

      <div className="relative z-10 flex min-h-screen items-center justify-center px-4 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-2xl"
        >
          <GlassCard padding="lg" className="shadow-2xl shadow-indigo-900/10">
            {/* Header */}
            <div className="text-center mb-8">
              <div className="mb-4 flex justify-center">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--accent-muted)] border border-[var(--accent)]/20">
                  <UserPlus className="h-7 w-7 text-[var(--accent)]" />
                </div>
              </div>
              <Badge className="mx-auto mb-3">Step 1 of 2</Badge>
              <h1 className="text-2xl font-bold text-[var(--text-primary)]">
                Create your account
              </h1>
              <p className="text-sm text-[var(--text-muted)] mt-1">
                Start your journey in seconds.
              </p>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                onSubmit();
              }}
              className="space-y-5"
            >
              <FormMessage message={error} type="error" className="text-center" />
              <FormMessage
                message={success ? "Signup successful!" : ""}
                type="success"
                className="text-center"
              />

              <div className="space-y-1.5">
                <Label htmlFor="signup-name">Full Name</Label>
                <Input
                  id="signup-name"
                  name="name"
                  placeholder="John Doe"
                  value={form.name}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="signup-email">Email</Label>
                <Input
                  id="signup-email"
                  name="email"
                  type="email"
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="signup-password">Password</Label>
                  <div className="relative">
                    <Input
                      id="signup-password"
                      name="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="••••••••"
                      value={form.password}
                      onChange={handleChange}
                      className="pr-10"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 right-0 flex items-center pr-3 text-[var(--text-dimmed)] transition-colors hover:text-[var(--text-secondary)]"
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="signup-confirm">Confirm</Label>
                  <div className="relative">
                    <Input
                      id="signup-confirm"
                      name="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="••••••••"
                      value={form.confirmPassword}
                      onChange={handleChange}
                      className="pr-10"
                      required
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setShowConfirmPassword(!showConfirmPassword)
                      }
                      className="absolute inset-y-0 right-0 flex items-center pr-3 text-[var(--text-dimmed)] transition-colors hover:text-[var(--text-secondary)]"
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="signup-phone">Phone</Label>
                  <Input
                    id="signup-phone"
                    name="phoneNo"
                    placeholder="+1234567890"
                    value={form.phoneNo}
                    onChange={handleChange}
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="signup-role">Role</Label>
                  <select
                    id="signup-role"
                    name="role"
                    value={form.role}
                    onChange={handleChange}
                    className="flex h-10 w-full appearance-none rounded-xl border px-3 py-2 text-sm outline-none transition bg-[rgba(255,255,255,0.04)] border-[var(--border-default)] text-[var(--text-primary)] focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent-muted)]"
                  >
                    <option value="STUDENT">Student</option>
                    <option value="TEACHER">Teacher</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="signup-dob">Date of Birth</Label>
                  <Input
                    id="signup-dob"
                    name="dateOfBirth"
                    type="date"
                    value={form.dateOfBirth}
                    onChange={handleChange}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="signup-pincode">Pincode</Label>
                  <Input
                    id="signup-pincode"
                    name="pincode"
                    placeholder="100001"
                    value={form.pincode}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
                <div className="space-y-1.5">
                  <Label htmlFor="signup-city">City</Label>
                  <Input
                    id="signup-city"
                    name="city"
                    placeholder="New York"
                    value={form.city}
                    onChange={handleChange}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="signup-state">State</Label>
                  <Input
                    id="signup-state"
                    name="state"
                    placeholder="NY"
                    value={form.state}
                    onChange={handleChange}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="signup-country">Country</Label>
                  <Input
                    id="signup-country"
                    name="country"
                    placeholder="USA"
                    value={form.country}
                    onChange={handleChange}
                  />
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
                    Create Account
                    <ArrowRight className="h-4 w-4 ml-1" />
                  </>
                )}
              </Button>
            </form>

            <p className="mt-7 text-center text-sm text-[var(--text-muted)]">
              Already have an account?{" "}
              <a
                href="/login"
                className="font-medium text-[var(--accent)] transition-colors hover:text-[var(--accent-hover)]"
              >
                Sign in
              </a>
            </p>
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
};

export default SignUpPage;
