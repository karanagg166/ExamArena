"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { api } from "@/lib/axios";
import { SignUpForm } from "@/types/user";
import { useAuthStore } from "@/stores";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { FormMessage } from "@/components/ui/form-message";
type ValidationError = {
  msg: string;
};

const SignUpPage = () => {
  const router = useRouter();
  const { login } = useAuthStore();
  const [form, setForm] = useState<SignUpForm>({
    name: "karan",
    email: "karan@gmail.com",
    password: "karan166",
    confirmPassword: "karan166",
    phoneNo: "+1234567890",
    dateOfBirth: "2000-01-01",
    role: "TEACHER",
    pincode: "100001",
    city: "New York",
    state: "NY",
    country: "USA",
  });

  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  // NEW: State for toggling password visibility
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Handle input change
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;

    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Submit handler
  const onSubmit = async () => {
    if (loading) return;

    const { name, email, password, confirmPassword } = form;

    // Validation
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
      // The backend UserRequest now perfectly matches the frontend form
      const { confirmPassword, ...payload } = form;
      void confirmPassword; // To prevent unused variable warning

      const data = await api.post("/api/v1/auth/signup", payload);
      console.log("Signup response:", data);

      setSuccess(true);
      toast.success("Account created successfully");
      // Redirect to role-specific profile setup
      login(form.email, form.password);
      router.push(`/signup/${form.role.toLowerCase()}`);
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        if (Array.isArray(detail)) {
          // Handle FastAPI Pydantic validation errors (array of objects)
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
    <div className="page-shell flex min-h-screen items-center justify-center py-12 text-white">
      <Card className="w-full max-w-2xl shadow-2xl shadow-indigo-950/20">
        <CardHeader className="text-center">
          <Badge className="mx-auto">Step 1 of 2</Badge>
          <CardTitle className="text-3xl">Create your account</CardTitle>
          <CardDescription>Start your journey in seconds.</CardDescription>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              onSubmit();
            }}
            className="space-y-4"
          >
            <FormMessage message={error} type="error" className="text-center" />
            <FormMessage
              message={success ? "Signup successful!" : ""}
              type="success"
              className="text-center"
            />

            <div>
              <Label className="mb-1.5 ml-1 block">Full Name</Label>
              <Input name="name" value={form.name} onChange={handleChange} />
            </div>

            <div>
              <Label className="mb-1.5 ml-1 block">Email</Label>
              <Input
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <Label className="mb-1.5 ml-1 block">Password</Label>
                <div className="relative">
                  <Input
                    name="password"
                    type={showPassword ? "text" : "password"}
                    value={form.password}
                    onChange={handleChange}
                    className="pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 text-zinc-500 transition-colors hover:text-zinc-300"
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              <div>
                <Label className="mb-1.5 ml-1 block">Confirm</Label>
                <div className="relative">
                  <Input
                    name="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    value={form.confirmPassword}
                    onChange={handleChange}
                    className="pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute inset-y-0 right-0 pr-3 text-zinc-500 transition-colors hover:text-zinc-300"
                  >
                    {showConfirmPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <Label className="mb-1.5 ml-1 block">Phone</Label>
                <Input
                  name="phoneNo"
                  value={form.phoneNo}
                  onChange={handleChange}
                />
              </div>

              <div>
                <Label className="mb-1.5 ml-1 block">Role</Label>
                <select
                  name="role"
                  value={form.role}
                  onChange={handleChange}
                  className="flex h-10 w-full appearance-none rounded-xl border border-zinc-700 bg-zinc-900/80 px-3 py-2 text-sm text-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
                >
                  <option value="STUDENT">Student</option>
                  <option value="TEACHER">Teacher</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input
                name="pincode"
                placeholder="Pincode"
                value={form.pincode}
                onChange={handleChange}
              />
              <Input
                name="city"
                placeholder="City"
                value={form.city}
                onChange={handleChange}
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input
                name="state"
                placeholder="State"
                value={form.state}
                onChange={handleChange}
              />
              <Input
                name="country"
                placeholder="Country"
                value={form.country}
                onChange={handleChange}
              />
            </div>

            <Button type="submit" disabled={loading} className="mt-2 w-full">
              {loading ? "Creating account..." : "Create Account"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default SignUpPage;
