"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { api } from "@/lib/axios";
import { School } from "@/types/school";

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
import { useSchoolClassStore } from "@/stores";
import {
  blockNonAlpha,
  blockNonPhone,
  blockNonDigits,
  sanitizeAlpha,
  sanitizePhoneNo,
  sanitizeNumber,
  validateEmailField,
  validatePhoneField,
  validateNameField,
} from "@/lib/utils";

export default function SignupStudentPage() {
  const router = useRouter();
  const [schools, setSchools] = useState<School[]>([]);

  const { fetchClassesBySchool, clearClasses, classes } = useSchoolClassStore();

  const [contactType, setContactType] = useState<"father" | "mother" | "guardian">("father");
  const [form, setForm] = useState({
    rollNo: "",
    schoolId: "",
    classId: "",
    fatherName: "",
    fatherEmail: "",
    fatherPhoneNo: "",
    motherName: "",
    motherEmail: "",
    motherPhoneNo: "",
    guardianName: "",
    guardianRelation: "",
    guardianEmail: "",
    guardianPhoneNo: "",
  });
  const [touched, setTouched] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/api/v1/schools/")
      .then((r) => setSchools(r.data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!form.schoolId) {
      clearClasses();
      return;
    }

    setForm((p) => ({ ...p, classId: "" }));
    fetchClassesBySchool(form.schoolId);
  }, [form.schoolId, fetchClassesBySchool, clearClasses]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    let sanitizedValue = value;
    if (name.endsWith("Name")) {
      sanitizedValue = sanitizeAlpha(value);
    } else if (name.endsWith("PhoneNo")) {
      sanitizedValue = sanitizePhoneNo(value);
    } else if (name === "rollNo") {
      sanitizedValue = sanitizeNumber(value);
    }
    setForm((p) => ({ ...p, [name]: sanitizedValue }));
  };

  const getFieldErrors = () => {
    const errors: Record<string, string | undefined> = {};
    if (contactType === "father") {
      errors.fatherName = validateNameField(form.fatherName, "Father's Name", true);
      errors.fatherEmail = validateEmailField(form.fatherEmail, true);
      errors.fatherPhoneNo = validatePhoneField(form.fatherPhoneNo, false);
    } else if (contactType === "mother") {
      errors.motherName = validateNameField(form.motherName, "Mother's Name", true);
      errors.motherEmail = validateEmailField(form.motherEmail, true);
      errors.motherPhoneNo = validatePhoneField(form.motherPhoneNo, false);
    } else if (contactType === "guardian") {
      errors.guardianName = validateNameField(form.guardianName, "Guardian Name", true);
      errors.guardianEmail = validateEmailField(form.guardianEmail, true);
      errors.guardianPhoneNo = validatePhoneField(form.guardianPhoneNo, false);
    }
    return errors;
  };

  const fieldErrors = getFieldErrors();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);

    if (!form.classId) {
      const message = "Please select a class.";
      setError(message);
      toast.error(message);
      return;
    }

    const currentErrors = getFieldErrors();
    if (Object.values(currentErrors).some(Boolean)) {
      toast.error("Please fix invalid fields before submitting.");
      return;
    }

    setSaving(true);
    setError("");

    const computedParentName =
      contactType === "father"
        ? form.fatherName
        : contactType === "mother"
          ? form.motherName
          : form.guardianName;

    const computedParentEmail =
      contactType === "father"
        ? form.fatherEmail
        : contactType === "mother"
          ? form.motherEmail
          : form.guardianEmail;

    try {
      await api.post("/api/v1/students/", {
        rollNo: form.rollNo,
        schoolId: form.schoolId,
        classId: form.classId,
        parentName: computedParentName,
        parentEmail: computedParentEmail,
        fatherName: form.fatherName || undefined,
        fatherEmail: form.fatherEmail || undefined,
        fatherPhoneNo: form.fatherPhoneNo || undefined,
        motherName: form.motherName || undefined,
        motherEmail: form.motherEmail || undefined,
        motherPhoneNo: form.motherPhoneNo || undefined,
        guardianName: form.guardianName || undefined,
        guardianRelation: form.guardianRelation || undefined,
        guardianEmail: form.guardianEmail || undefined,
        guardianPhoneNo: form.guardianPhoneNo || undefined,
      });
      toast.success("Student profile completed");
      router.push("/student");
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        const message =
          typeof detail === "string" ? detail : "Failed to create profile.";
        setError(message);
        toast.error(message);
      }
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
            Complete your Student profile
          </CardTitle>
          <CardDescription>
            Select your school, class, and parent/guardian contact details.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <FormMessage message={error} type="error" />

            <div>
              <Label className="mb-1.5 block">Select School</Label>
              <select
                name="schoolId"
                value={form.schoolId}
                onChange={handleChange}
                required
                className="flex h-10 w-full appearance-none rounded-xl border border-zinc-700 bg-zinc-900/80 px-3 py-2 text-sm text-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
              >
                <option value="">— Choose your school —</option>
                {schools.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                    {s.city ? ` — ${s.city}` : ""}
                  </option>
                ))}
              </select>
            </div>

            {form.schoolId && (
              <div>
                <Label className="mb-1.5 block">Select Class</Label>
                <select
                  name="classId"
                  value={form.classId}
                  onChange={handleChange}
                  required
                  className="flex h-10 w-full appearance-none rounded-xl border border-zinc-700 bg-zinc-900/80 px-3 py-2 text-sm text-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
                >
                  <option value="">— Choose your class —</option>
                  {classes.length === 0 ? (
                    <option disabled>
                      No classes available for this school yet
                    </option>
                  ) : (
                    classes.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))
                  )}
                </select>
              </div>
            )}

            <div>
              <Label className="mb-1.5 block">Roll Number</Label>
              <Input
                name="rollNo"
                value={form.rollNo}
                onKeyDown={blockNonDigits}
                onChange={handleChange}
                required
              />
            </div>

            {/* Parent / Guardian Selection */}
            <div className="border-t border-zinc-800 pt-4 mt-4 space-y-4">
              <Label className="block font-semibold text-zinc-200">
                Primary Parent / Guardian Contact
              </Label>
              <div className="flex gap-2 p-1 bg-zinc-900 rounded-xl border border-zinc-800">
                <button
                  type="button"
                  onClick={() => setContactType("father")}
                  className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
                    contactType === "father"
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "text-zinc-400 hover:text-white"
                  }`}
                >
                  Father
                </button>
                <button
                  type="button"
                  onClick={() => setContactType("mother")}
                  className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
                    contactType === "mother"
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "text-zinc-400 hover:text-white"
                  }`}
                >
                  Mother
                </button>
                <button
                  type="button"
                  onClick={() => setContactType("guardian")}
                  className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
                    contactType === "guardian"
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "text-zinc-400 hover:text-white"
                  }`}
                >
                  Guardian
                </button>
              </div>

              {contactType === "father" && (
                <div className="space-y-3 p-4 rounded-xl bg-zinc-900/50 border border-zinc-800 animate-in fade-in duration-300">
                  <h4 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                    Father&apos;s Information
                  </h4>
                  <div>
                    <Label className="mb-1 block text-xs">Father&apos;s Name</Label>
                    <Input
                      name="fatherName"
                      value={form.fatherName}
                      onChange={handleChange}
                      onKeyDown={blockNonAlpha}
                      error={touched || form.fatherName ? fieldErrors.fatherName : undefined}
                      required
                      placeholder="e.g. John Doe"
                    />
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <Label className="mb-1 block text-xs">Father&apos;s Email</Label>
                      <Input
                        type="email"
                        name="fatherEmail"
                        value={form.fatherEmail}
                        onChange={handleChange}
                        error={touched || form.fatherEmail ? fieldErrors.fatherEmail : undefined}
                        required
                        placeholder="father@example.com"
                      />
                    </div>
                    <div>
                      <Label className="mb-1 block text-xs">Father&apos;s Phone Number</Label>
                      <Input
                        type="tel"
                        name="fatherPhoneNo"
                        value={form.fatherPhoneNo}
                        onKeyDown={blockNonPhone}
                        onChange={handleChange}
                        error={touched || form.fatherPhoneNo ? fieldErrors.fatherPhoneNo : undefined}
                        placeholder="+1 234 567 890"
                      />
                    </div>
                  </div>
                </div>
              )}

              {contactType === "mother" && (
                <div className="space-y-3 p-4 rounded-xl bg-zinc-900/50 border border-zinc-800 animate-in fade-in duration-300">
                  <h4 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                    Mother&apos;s Information
                  </h4>
                  <div>
                    <Label className="mb-1 block text-xs">Mother&apos;s Name</Label>
                    <Input
                      name="motherName"
                      value={form.motherName}
                      onChange={handleChange}
                      onKeyDown={blockNonAlpha}
                      error={touched || form.motherName ? fieldErrors.motherName : undefined}
                      required
                      placeholder="e.g. Jane Doe"
                    />
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <Label className="mb-1 block text-xs">Mother&apos;s Email</Label>
                      <Input
                        type="email"
                        name="motherEmail"
                        value={form.motherEmail}
                        onChange={handleChange}
                        error={touched || form.motherEmail ? fieldErrors.motherEmail : undefined}
                        required
                        placeholder="mother@example.com"
                      />
                    </div>
                    <div>
                      <Label className="mb-1 block text-xs">Mother&apos;s Phone Number</Label>
                      <Input
                        type="tel"
                        name="motherPhoneNo"
                        value={form.motherPhoneNo}
                        onKeyDown={blockNonPhone}
                        onChange={handleChange}
                        error={touched || form.motherPhoneNo ? fieldErrors.motherPhoneNo : undefined}
                        placeholder="+1 234 567 890"
                      />
                    </div>
                  </div>
                </div>
              )}

              {contactType === "guardian" && (
                <div className="space-y-3 p-4 rounded-xl bg-zinc-900/50 border border-zinc-800 animate-in fade-in duration-300">
                  <h4 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                    Guardian Information
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <Label className="mb-1 block text-xs">Guardian Name</Label>
                      <Input
                        name="guardianName"
                        value={form.guardianName}
                        onChange={handleChange}
                        onKeyDown={blockNonAlpha}
                        error={touched || form.guardianName ? fieldErrors.guardianName : undefined}
                        required
                        placeholder="e.g. Robert Smith"
                      />
                    </div>
                    <div>
                      <Label className="mb-1 block text-xs">Relation to Student</Label>
                      <Input
                        name="guardianRelation"
                        value={form.guardianRelation}
                        onChange={handleChange}
                        required
                        placeholder="e.g. Uncle / Grandparent"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <Label className="mb-1 block text-xs">Guardian Email</Label>
                      <Input
                        type="email"
                        name="guardianEmail"
                        value={form.guardianEmail}
                        onChange={handleChange}
                        error={touched || form.guardianEmail ? fieldErrors.guardianEmail : undefined}
                        required
                        placeholder="guardian@example.com"
                      />
                    </div>
                    <div>
                      <Label className="mb-1 block text-xs">Guardian Phone Number</Label>
                      <Input
                        type="tel"
                        name="guardianPhoneNo"
                        value={form.guardianPhoneNo}
                        onKeyDown={blockNonPhone}
                        onChange={handleChange}
                        error={touched || form.guardianPhoneNo ? fieldErrors.guardianPhoneNo : undefined}
                        placeholder="+1 234 567 890"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>

            <Button type="submit" disabled={saving} className="mt-2 w-full">
              {saving ? "Setting up…" : "Complete Setup →"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
