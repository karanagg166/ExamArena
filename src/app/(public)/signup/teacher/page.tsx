"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { api } from "@/lib/axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FormMessage } from "@/components/ui/form-message";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function SignupTeacherPage() {
  const router = useRouter();

  // Using string for experience initially to handle empty inputs cleanly
  const [form, setForm] = useState<{
    qualifications: string[];
    experience: string;
    department: string;
    subjects: string[];
  }>({
    qualifications: [],
    experience: "",
    department: "",
    subjects: [],
  });

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [availableQualifications, setAvailableQualifications] = useState<
    string[]
  >([]);
  const [availableSubjects, setAvailableSubjects] = useState<string[]>([]);

  useEffect(() => {
    // NOTE: Make sure your FastAPI backend has these matching routes!
    api
      .get("/api/v1/teachers/qualifications")
      .then((r) => setAvailableQualifications(r.data))
      .catch(console.error);
    api
      .get("/api/v1/teachers/subjects")
      .then((r) => setAvailableSubjects(r.data))
      .catch(console.error);
  }, []);

  const toggleSelection = (
    field: "qualifications" | "subjects",
    value: string,
  ) => {
    setForm((prev) => {
      const currentSelected = prev[field];
      if (currentSelected.includes(value)) {
        return {
          ...prev,
          [field]: currentSelected.filter((item) => item !== value),
        };
      } else {
        return { ...prev, [field]: [...currentSelected, value] };
      }
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");

    // Simple validation to ensure they selected at least one qualification
    if (form.qualifications.length === 0) {
      const message = "Please select at least one qualification.";
      setError(message);
      toast.error(message);
      setSaving(false);
      return;
    }
    console.log("Submitting teacher profile with data:", form);
    try {
      const data = await api.post("/api/v1/teachers/", {
        qualifications: form.qualifications,
        experience: parseInt(form.experience) || 0,
        department: form.department,
        subjects: form.subjects,
      });
      console.log("Teacher profile created successfully:", data);
      toast.success("Teacher profile completed");
      router.push("/dashboard");
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        const message =
          typeof detail === "string" ? detail : "Failed to create profile.";
        setError(message);
        toast.error(message);
      }
      console.error("Error creating teacher profile:", err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-shell flex min-h-screen items-center justify-center py-12 text-white">
      <Card className="w-full max-w-xl shadow-2xl shadow-indigo-950/20">
        <CardHeader>
          <Badge className="w-fit uppercase tracking-widest">Step 2 of 2</Badge>
          <CardTitle className="text-2xl">
            Complete your Teacher profile
          </CardTitle>
          <CardDescription>
            Tell us about your professional background.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <FormMessage message={error} type="error" />

            {/* Basic Info Section */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <Label className="mb-1.5 block">Department</Label>
                <Input
                  value={form.department}
                  onChange={(e) =>
                    setForm((p) => ({ ...p, department: e.target.value }))
                  }
                  placeholder="e.g. Mathematics"
                  required
                />
              </div>
              <div>
                <Label className="mb-1.5 block">Years of Experience</Label>
                <Input
                  type="number"
                  min="0"
                  value={form.experience}
                  onChange={(e) =>
                    setForm((p) => ({ ...p, experience: e.target.value }))
                  }
                  required
                />
              </div>
            </div>

            <hr className="border-zinc-800" />

            {/* Qualifications Multi-Select */}
            <div>
              <Label className="mb-2 block">Qualifications & Degrees</Label>
              <div className="flex flex-wrap gap-2">
                {availableQualifications.length > 0 ? (
                  availableQualifications.map((qual) => (
                    <Button
                      key={qual}
                      type="button"
                      onClick={() => toggleSelection("qualifications", qual)}
                      variant={
                        form.qualifications.includes(qual)
                          ? "primary"
                          : "outline"
                      }
                      className="h-9"
                    >
                      {qual}
                    </Button>
                  ))
                ) : (
                  <p className="text-sm text-zinc-500 italic">
                    Loading qualifications...
                  </p>
                )}
              </div>
            </div>

            {/* Subjects Multi-Select */}
            <div>
              <Label className="mb-2 block">Teaching Subjects</Label>
              <div className="flex flex-wrap gap-2">
                {availableSubjects.length > 0 ? (
                  availableSubjects.map((sub) => (
                    <Button
                      key={sub}
                      type="button"
                      onClick={() => toggleSelection("subjects", sub)}
                      variant={
                        form.subjects.includes(sub) ? "primary" : "outline"
                      }
                      className="h-9"
                    >
                      {sub}
                    </Button>
                  ))
                ) : (
                  <p className="text-sm text-zinc-500 italic">
                    Loading subjects...
                  </p>
                )}
              </div>
            </div>

            <Button
              type="submit"
              disabled={saving}
              className="mt-4 w-full"
              size="lg"
            >
              {saving ? "Setting up…" : "Complete Setup →"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
