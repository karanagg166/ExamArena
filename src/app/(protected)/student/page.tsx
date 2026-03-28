"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { api } from "@/lib/axios";
import { Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FormMessage } from "@/components/ui/form-message";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/loading";

export default function ProfileStudentPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    rollNo: "",
    dob: "",
    parentName: "",
    parentEmail: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(
    null,
  );

  useEffect(() => {
    api
      .get("/api/v1/students/me")
      .then((r) => {
        const d = r.data;
        setForm({
          rollNo: d.rollNo ?? "",
          dob: d.dob ? d.dob.split("T")[0] : "",
          parentName: d.parentName ?? "",
          parentEmail: d.parentEmail ?? "",
        });
      })
      .catch(() => router.push("/login"))
      .finally(() => setLoading(false));
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      await api.put("/api/v1/students/me", {
        rollNo: form.rollNo,
        dob: new Date(form.dob).toISOString(),
        parentName: form.parentName,
        parentEmail: form.parentEmail,
      });
      setMessage({ text: "Student profile updated!", ok: true });
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        setMessage({
          text: typeof detail === "string" ? detail : "Update failed.",
          ok: false,
        });
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading)
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-8 w-8 border-4" />
      </div>
    );

  return (
    <div className="page-shell text-white">
      <div className="mx-auto max-w-2xl">
        <div className="mb-8">
          <h1 className="page-title">Student Profile</h1>
          <p className="page-subtitle">Update your student-specific details.</p>
        </div>

        <FormMessage
          message={message?.text}
          type={message?.ok ? "success" : "error"}
          className="mb-5 text-center"
        />

        <Card>
          <CardHeader>
            <CardTitle>Profile Details</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label className="mb-1 block">Roll Number</Label>
                <Input
                  value={form.rollNo}
                  onChange={(e) =>
                    setForm((p) => ({ ...p, rollNo: e.target.value }))
                  }
                  required
                />
              </div>
              <div>
                <Label className="mb-1 block">Date of Birth</Label>
                <Input
                  type="date"
                  value={form.dob}
                  onChange={(e) =>
                    setForm((p) => ({ ...p, dob: e.target.value }))
                  }
                  required
                />
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <Label className="mb-1 block">Parent Name</Label>
                  <Input
                    value={form.parentName}
                    onChange={(e) =>
                      setForm((p) => ({ ...p, parentName: e.target.value }))
                    }
                  />
                </div>
                <div>
                  <Label className="mb-1 block">Parent Email</Label>
                  <Input
                    type="email"
                    value={form.parentEmail}
                    onChange={(e) =>
                      setForm((p) => ({ ...p, parentEmail: e.target.value }))
                    }
                  />
                </div>
              </div>
              <div className="flex flex-wrap gap-3 pt-2">
                <Button type="submit" disabled={saving} className="gap-2">
                  <Save className="h-4 w-4" />
                  {saving ? "Saving..." : "Save Changes"}
                </Button>
                <Button asChild variant="secondary">
                  <a href="/profile">Account Settings</a>
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
