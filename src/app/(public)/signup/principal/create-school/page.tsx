"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { api } from "@/lib/axios";
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

type SchoolType = "PUBLIC" | "PRIVATE" | "CHARTER" | "INTERNATIONAL";

type FormState = {
  name: string;
  address: string;
  city: string;
  state: string;
  country: string;
  pincode: string;
  schoolCode: string;
  type: SchoolType;
  email: string;
  website: string;
};

const INITIAL_FORM: FormState = {
  name: "",
  address: "",
  city: "",
  state: "",
  country: "",
  pincode: "",
  schoolCode: "",
  type: "PUBLIC",
  email: "",
  website: "",
};

export default function PrincipalCreateSchoolPage() {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError(null);

    try {
      await api.post("/api/v1/schools/", {
        ...form,
        email: form.email.trim() || undefined,
        website: form.website.trim() || undefined,
      });
      router.push("/principal");
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        setError(
          typeof detail === "string"
            ? detail
            : (err.message ?? "Something went wrong"),
        );
      } else {
        setError("Something went wrong");
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-shell flex min-h-screen items-center justify-center py-12 text-white">
      <Card className="w-full max-w-3xl shadow-2xl shadow-indigo-950/20">
        <CardHeader>
          <CardTitle className="text-2xl">Create a New School</CardTitle>
          <CardDescription>
            Fill this form to create a school and complete principal setup.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">
            {error ? (
              <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
                {error}
              </p>
            ) : null}

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <Label className="mb-1.5 block">School Name</Label>
                <Input
                  value={form.name}
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, name: event.target.value }))
                  }
                  required
                />
              </div>
              <div>
                <Label className="mb-1.5 block">School Code</Label>
                <Input
                  value={form.schoolCode}
                  onChange={(event) =>
                    setForm((prev) => ({
                      ...prev,
                      schoolCode: event.target.value,
                    }))
                  }
                  required
                />
              </div>
            </div>

            <div>
              <Label className="mb-1.5 block">Address</Label>
              <Input
                value={form.address}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, address: event.target.value }))
                }
                required
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <Label className="mb-1.5 block">City</Label>
                <Input
                  value={form.city}
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, city: event.target.value }))
                  }
                  required
                />
              </div>
              <div>
                <Label className="mb-1.5 block">State</Label>
                <Input
                  value={form.state}
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, state: event.target.value }))
                  }
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <Label className="mb-1.5 block">Country</Label>
                <Input
                  value={form.country}
                  onChange={(event) =>
                    setForm((prev) => ({
                      ...prev,
                      country: event.target.value,
                    }))
                  }
                  required
                />
              </div>
              <div>
                <Label className="mb-1.5 block">Pincode</Label>
                <Input
                  value={form.pincode}
                  onChange={(event) =>
                    setForm((prev) => ({
                      ...prev,
                      pincode: event.target.value,
                    }))
                  }
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <Label className="mb-1.5 block">Type</Label>
                <select
                  value={form.type}
                  onChange={(event) =>
                    setForm((prev) => ({
                      ...prev,
                      type: event.target.value as SchoolType,
                    }))
                  }
                  className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="PUBLIC">Public</option>
                  <option value="PRIVATE">Private</option>
                  <option value="CHARTER">Charter</option>
                  <option value="INTERNATIONAL">International</option>
                </select>
              </div>
              <div>
                <Label className="mb-1.5 block">Email (optional)</Label>
                <Input
                  value={form.email}
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, email: event.target.value }))
                  }
                />
              </div>
              <div>
                <Label className="mb-1.5 block">Website (optional)</Label>
                <Input
                  value={form.website}
                  onChange={(event) =>
                    setForm((prev) => ({
                      ...prev,
                      website: event.target.value,
                    }))
                  }
                />
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={saving}>
              {saving ? "Creating School..." : "Create School"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
