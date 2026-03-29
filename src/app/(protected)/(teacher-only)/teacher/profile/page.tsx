"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { GraduationCap, Edit2, Save, X } from "lucide-react";
import { api } from "@/lib/axios";
import type { Teacher } from "@/types";
import { toast } from "sonner";
import { Spinner } from "@/components/ui/loading";

type TeacherForm = Pick<
  Teacher,
  "qualifications" | "experience" | "department" | "subjects"
>;

const toStringArray = (value: unknown): string[] => {
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean);
  }

  if (typeof value === "string") {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return [];
};

const hasValue = (arr: string[], value: string): boolean => {
  return arr.some((item) => item.toLowerCase() === value.toLowerCase());
};

export default function TeacherDashboard() {
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<TeacherForm>({
    qualifications: [],
    experience: 0,
    department: "",
    subjects: [],
  });
  const [availableQualifications, setAvailableQualifications] = useState<
    string[]
  >([]);
  const [availableSubjects, setAvailableSubjects] = useState<string[]>([]);
  const router = useRouter();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.get("/api/v1/teachers/me", {
          withCredentials: true,
        });
        const data = response.data;
        console.log("Fetched teacher data:", data);
        setFormData({
          qualifications: toStringArray(
            data.qualifications ?? data.qualification,
          ),
          experience: data.experience || 0,
          department: data.department || "",
          subjects: toStringArray(data.subjects),
        });
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [router]);

  useEffect(() => {
    api
      .get("/api/v1/teachers/qualifications")
      .then((r) => setAvailableQualifications(r.data || []))
      .catch(console.error);

    api
      .get("/api/v1/teachers/subjects")
      .then((r) => setAvailableSubjects(r.data || []))
      .catch(console.error);
  }, []);

  const toggleSelection = (
    field: "qualifications" | "subjects",
    value: string,
  ) => {
    setFormData((prev) => {
      const selected = prev[field];
      return hasValue(selected, value)
        ? {
            ...prev,
            [field]: selected.filter(
              (item) => item.toLowerCase() !== value.toLowerCase(),
            ),
          }
        : { ...prev, [field]: [...selected, value] };
    });
  };

  const handleSave = async () => {
    try {
      await api.put(
        "/api/v1/teachers/me",
        {
          qualifications: formData.qualifications,
          experience: formData.experience,
          department: formData.department,
          subjects: formData.subjects,
        },
        { withCredentials: true },
      );

      setIsEditing(false);
      toast.success("Profile updated successfully!");
    } catch (error) {
      console.error("Error saving data:", error);
      toast.error("Failed to update profile. Please try again.");
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-8 w-8 border-4" />
      </div>
    );
  }

  return (
    <div className="page-shell text-white">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Teacher Professional Profile</h1>
            <p className="text-zinc-400 mt-1">
              Manage qualifications, subjects, and department.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <a
              href="/profile"
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors text-sm"
            >
              Edit Personal Info
            </a>
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
            >
              {isEditing ? (
                <X className="w-4 h-4" />
              ) : (
                <Edit2 className="w-4 h-4" />
              )}
              {isEditing ? "Cancel" : "Edit Profile"}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6">
          <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-6 max-w-3xl">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <GraduationCap className="w-5 h-5 text-indigo-400" />
              Professional Details
            </h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-zinc-400 block mb-2">
                  Qualifications
                </label>
                <div className="flex flex-wrap gap-2">
                  {availableQualifications.length > 0 ? (
                    availableQualifications.map((qual) => (
                      <button
                        key={qual}
                        type="button"
                        disabled={!isEditing}
                        onClick={() => toggleSelection("qualifications", qual)}
                        className={`px-3 py-2 rounded-lg text-sm border transition-colors ${
                          hasValue(formData.qualifications, qual)
                            ? "bg-indigo-600/20 text-indigo-300 border-indigo-500/50"
                            : "bg-zinc-900 text-zinc-400 border-zinc-800 hover:bg-zinc-800"
                        } disabled:opacity-50 disabled:cursor-not-allowed`}
                      >
                        {qual}
                      </button>
                    ))
                  ) : (
                    <p className="text-sm text-zinc-500">
                      No qualifications available.
                    </p>
                  )}
                </div>
              </div>
              <div>
                <label className="text-sm text-zinc-400">
                  Experience (years)
                </label>
                <input
                  type="number"
                  value={formData.experience}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      experience: parseInt(e.target.value) || 0,
                    })
                  }
                  disabled={!isEditing}
                  className="w-full mt-1 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 disabled:opacity-50"
                />
              </div>
              <div>
                <label className="text-sm text-zinc-400">Department</label>
                <input
                  type="text"
                  value={formData.department}
                  onChange={(e) =>
                    setFormData({ ...formData, department: e.target.value })
                  }
                  disabled={!isEditing}
                  placeholder="e.g., Mathematics"
                  className="w-full mt-1 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 disabled:opacity-50"
                />
              </div>
              <div>
                <label className="text-sm text-zinc-400 block mb-2">
                  Subjects
                </label>
                <div className="flex flex-wrap gap-2">
                  {availableSubjects.length > 0 ? (
                    availableSubjects.map((subject) => (
                      <button
                        key={subject}
                        type="button"
                        disabled={!isEditing}
                        onClick={() => toggleSelection("subjects", subject)}
                        className={`px-3 py-2 rounded-lg text-sm border transition-colors ${
                          hasValue(formData.subjects, subject)
                            ? "bg-indigo-600/20 text-indigo-300 border-indigo-500/50"
                            : "bg-zinc-900 text-zinc-400 border-zinc-800 hover:bg-zinc-800"
                        } disabled:opacity-50 disabled:cursor-not-allowed`}
                      >
                        {subject}
                      </button>
                    ))
                  ) : (
                    <p className="text-sm text-zinc-500">
                      No subjects available.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {isEditing && (
          <div className="mt-6 flex justify-end">
            <button
              onClick={handleSave}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
            >
              <Save className="w-4 h-4" />
              Save Changes
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
