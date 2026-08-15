"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAxiosError } from "axios";
import { Save, ArrowRight } from "lucide-react";
import { api } from "@/lib/axios";
import { User } from "@/types/user";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/ui/page-header";
import { Spinner } from "@/components/ui/loading";
import { FormMessage } from "@/components/ui/form-message";
import { ChangePasswordForm } from "@/components/profile/ChangePasswordForm";
import {
  sanitizePincode,
  sanitizePhoneNo,
  sanitizeAlpha,
  blockNonDigits,
  blockNonPhone,
  blockNonAlpha,
  validateEmailField,
  validatePhoneField,
  validatePincodeField,
  validateNameField,
} from "@/lib/utils";

// All user fields except id, role, and server timestamps
type UserForm = Omit<User, "id" | "role" | "createdAt" | "updatedAt">;

export default function ProfilePage() {
  const router = useRouter();
  const [role, setRole] = useState<User["role"] | null>(null);
  const [form, setForm] = useState<UserForm>({
    name: "",
    email: "",
    phoneNo: "",
    dateOfBirth: "",
    city: "",
    state: "",
    country: "",
    pincode: "",
  });
  const [touched, setTouched] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(
    null,
  );

  const getFieldErrors = () => {
    return {
      name: validateNameField(form.name, "Full Name", true),
      email: validateEmailField(form.email, true),
      phoneNo: validatePhoneField(form.phoneNo, false),
      pincode: validatePincodeField(form.pincode, false),
    };
  };

  const fieldErrors = getFieldErrors();

  useEffect(() => {
    api
      .get("/api/v1/auth/me")
      .then((r) => {
        const d = r.data as User;
        setRole(d.role ?? null);
        setForm({
          name: d.name ?? "",
          email: d.email ?? "",
          phoneNo: d.phoneNo ?? "",
          dateOfBirth: d.dateOfBirth ?? "",
          city: d.city ?? "",
          state: d.state ?? "",
          country: d.country ?? "",
          pincode: d.pincode ?? "",
        });
      })
      .catch(() => router.push("/login"))
      .finally(() => setLoading(false));
  }, [router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    let sanitizedValue = value;
    if (name === "pincode") {
      sanitizedValue = sanitizePincode(value);
    } else if (name === "phoneNo") {
      sanitizedValue = sanitizePhoneNo(value);
    } else if (name === "name") {
      sanitizedValue = sanitizeAlpha(value);
    }
    setForm((p) => ({ ...p, [name]: sanitizedValue }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);

    const currentErrors = getFieldErrors();
    if (Object.values(currentErrors).some(Boolean)) {
      setMessage({
        text: "Please fix invalid fields before saving.",
        ok: false,
      });
      return;
    }

    setSaving(true);
    setMessage(null);
    try {
      await api.put("/api/v1/auth/me", form);
      setMessage({ text: "Profile updated successfully!", ok: true });
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        setMessage({
          text: typeof detail === "string" ? detail : "Failed to update.",
          ok: false,
        });
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Spinner className="h-8 w-8 border-4" />
      </div>
    );
  }

  return (
    <div className="page-shell animate-fade-in-up">
      <div className="max-w-2xl mx-auto">
        <PageHeader
          title="Account Settings"
          subtitle="Update your personal information."
        />

        <div className="mt-8">
          {message && (
            <FormMessage
              message={message.text}
              type={message.ok ? "success" : "error"}
              className="mb-6 text-center"
            />
          )}

          <form
            onSubmit={handleSubmit}
            className="panel panel-padding space-y-5"
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div className="space-y-1.5">
                <Label htmlFor="profile-name">Full Name</Label>
                <Input
                  id="profile-name"
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  onKeyDown={blockNonAlpha}
                  error={touched || form.name ? fieldErrors.name : undefined}
                  required
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="profile-email">Email</Label>
                <Input
                  id="profile-email"
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  error={touched || form.email ? fieldErrors.email : undefined}
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div className="space-y-1.5">
                <Label htmlFor="profile-phone">Phone Number</Label>
                <Input
                  id="profile-phone"
                  name="phoneNo"
                  type="tel"
                  inputMode="tel"
                  value={form.phoneNo}
                  onChange={handleChange}
                  onKeyDown={blockNonPhone}
                  error={touched || form.phoneNo ? fieldErrors.phoneNo : undefined}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="profile-dob">Date of Birth</Label>
                <Input
                  id="profile-dob"
                  type="date"
                  name="dateOfBirth"
                  value={form.dateOfBirth}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div className="space-y-1.5">
                <Label htmlFor="profile-city">City</Label>
                <Input
                  id="profile-city"
                  name="city"
                  value={form.city}
                  onChange={handleChange}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="profile-pincode">Pincode</Label>
                <Input
                  id="profile-pincode"
                  name="pincode"
                  inputMode="numeric"
                  maxLength={6}
                  value={form.pincode}
                  onChange={handleChange}
                  onKeyDown={blockNonDigits}
                  error={touched || form.pincode ? fieldErrors.pincode : undefined}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div className="space-y-1.5">
                <Label htmlFor="profile-state">State</Label>
                <Input
                  id="profile-state"
                  name="state"
                  value={form.state}
                  onChange={handleChange}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="profile-country">Country</Label>
                <Input
                  id="profile-country"
                  name="country"
                  value={form.country}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-3 pt-2">
              <Button type="submit" disabled={saving}>
                <Save className="h-4 w-4" />
                {saving ? "Saving…" : "Save Changes"}
              </Button>
              {role && (
                <Button asChild variant="secondary">
                  <a href={`/${role.toLowerCase()}/profile`}>
                    Edit {role.charAt(0) + role.slice(1).toLowerCase()} Info
                    <ArrowRight className="h-4 w-4 ml-1" />
                  </a>
                </Button>
              )}
            </div>
          </form>

          <ChangePasswordForm />
        </div>
      </div>
    </div>
  );
}
