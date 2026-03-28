"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { api } from "@/lib/axios";
import { Save } from "lucide-react";
import { Teacher } from "@/types/teacher";

const INPUT_CLS =
  "w-full bg-zinc-900 border border-zinc-800 text-white rounded-xl py-2.5 px-4 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all disabled:opacity-50";
type TeacherForm = Pick<
  Teacher,
  "qualifications" | "experience" | "department" | "subjects"
>;

export default function ProfileTeacherPage() {
  const router = useRouter();

  const [form, setForm] = useState<TeacherForm>({
    qualifications: [],
    experience: 0,
    department: "",
    subjects: [],
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(
    null,
  );

  // State to hold the available options fetched from the backend
  const [availableQualifications, setAvailableQualifications] = useState<
    string[]
  >([]);
  const [availableSubjects, setAvailableSubjects] = useState<string[]>([]);

  useEffect(() => {
    // Fetch teacher's current profile
    api
      .get("/api/v1/teachers/me")
      .then((r) => {
        const d = r.data;
        setForm({
          qualifications: d.qualifications ?? [],
          experience: d.experience ?? 0,
          department: d.department ?? "",
          subjects: d.subjects ?? [],
        });
      })
      .catch(() => router.push("/login"))
      .finally(() => setLoading(false));
  }, [router]);

  useEffect(() => {
    // Fetch available options from the backend
    api
      .get("/api/v1/teachers/qualifications")
      .then((r) => setAvailableQualifications(r.data))
      .catch(console.error);
    api
      .get("/api/v1/teachers/subjects")
      .then((r) => setAvailableSubjects(r.data))
      .catch(console.error);
  }, []);

  // Helper function to toggle multi-select options
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
    setMessage(null);
    try {
      await api.put("/api/v1/teachers/me", form);
      setMessage({ text: "Teacher profile updated!", ok: true });
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
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );

  return (
    <div className="min-h-screen bg-black text-white p-6">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Teacher Profile</h1>
          <p className="text-zinc-400 mt-1 text-sm">
            Update your professional details.
          </p>
        </div>

        {message && (
          <div
            className={`p-3 rounded-xl mb-5 text-sm text-center border ${
              message.ok
                ? "bg-green-500/10 text-green-400 border-green-500/20"
                : "bg-red-500/10 text-red-400 border-red-500/20"
            }`}
          >
            {message.text}
          </div>
        )}

        <form
          onSubmit={handleSubmit}
          className="bg-zinc-950 border border-zinc-800 rounded-2xl p-6 space-y-6"
        >
          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-zinc-400 block mb-1">
                Department
              </label>
              <input
                value={form.department}
                onChange={(e) =>
                  setForm((p) => ({ ...p, department: e.target.value }))
                }
                placeholder="e.g. Mathematics"
                className={INPUT_CLS}
              />
            </div>
            <div>
              <label className="text-sm text-zinc-400 block mb-1">
                Years of Experience
              </label>
              <input
                type="number"
                min="0"
                value={form.experience}
                onChange={(e) =>
                  setForm((p) => ({
                    ...p,
                    experience: parseInt(e.target.value) || 0,
                  }))
                }
                className={INPUT_CLS}
              />
            </div>
          </div>

          <hr className="border-zinc-800" />

          {/* Qualifications Multi-Select */}
          <div>
            <label className="text-sm font-medium text-zinc-300 block mb-2">
              Qualifications & Degrees
            </label>
            <div className="flex flex-wrap gap-2">
              {availableQualifications.length > 0 ? (
                availableQualifications.map((qual) => (
                  <button
                    key={qual}
                    type="button"
                    onClick={() => toggleSelection("qualifications", qual)}
                    className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 border ${
                      form.qualifications.includes(qual)
                        ? "bg-indigo-600/20 text-indigo-400 border-indigo-500/50"
                        : "bg-zinc-900 text-zinc-400 border-zinc-800 hover:bg-zinc-800 hover:text-zinc-200"
                    }`}
                  >
                    {qual}
                  </button>
                ))
              ) : (
                <p className="text-sm text-zinc-500 italic">
                  No qualifications available to select.
                </p>
              )}
            </div>
          </div>

          {/* Subjects Multi-Select */}
          <div>
            <label className="text-sm font-medium text-zinc-300 block mb-2">
              Teaching Subjects
            </label>
            <div className="flex flex-wrap gap-2">
              {availableSubjects.length > 0 ? (
                availableSubjects.map((sub) => (
                  <button
                    key={sub}
                    type="button"
                    onClick={() => toggleSelection("subjects", sub)}
                    className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 border ${
                      form.subjects.includes(sub)
                        ? "bg-indigo-600/20 text-indigo-400 border-indigo-500/50"
                        : "bg-zinc-900 text-zinc-400 border-zinc-800 hover:bg-zinc-800 hover:text-zinc-200"
                    }`}
                  >
                    {sub}
                  </button>
                ))
              ) : (
                <p className="text-sm text-zinc-500 italic">
                  No subjects available to select.
                </p>
              )}
            </div>
          </div>

          {/* Submit Area */}
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 rounded-xl font-semibold transition-all disabled:opacity-50 shadow-lg shadow-indigo-600/20"
            >
              <Save className="w-4 h-4" />
              {saving ? "Saving…" : "Save Changes"}
            </button>
            <button
              type="button"
              onClick={() => router.push("/profile")}
              className="flex items-center px-5 py-3 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 rounded-xl text-sm font-medium transition-all"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
