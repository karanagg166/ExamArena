"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { api } from "@/lib/axios";

const INPUT_CLS = "w-full bg-zinc-900 border border-zinc-800 text-white rounded-xl py-2.5 px-4 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all";

export default function SignupTeacherPage() {
    const router = useRouter();

    // Using string for experience initially to handle empty inputs cleanly
    const [form, setForm] = useState<{ qualifications: string[]; experience: string; department: string; subjects: string[] }>({
        qualifications: [],
        experience: "",
        department: "",
        subjects: []
    });

    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    const [availableQualifications, setAvailableQualifications] = useState<string[]>([]);
    const [availableSubjects, setAvailableSubjects] = useState<string[]>([]);

    useEffect(() => {
        // NOTE: Make sure your FastAPI backend has these matching routes!
        api.get("/api/v1/teachers/qualifications").then((r) => setAvailableQualifications(r.data)).catch(console.error);
        api.get("/api/v1/teachers/subjects").then((r) => setAvailableSubjects(r.data)).catch(console.error);
    }, []);

    const toggleSelection = (field: "qualifications" | "subjects", value: string) => {
        setForm((prev) => {
            const currentSelected = prev[field];
            if (currentSelected.includes(value)) {
                return { ...prev, [field]: currentSelected.filter((item) => item !== value) };
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
            setError("Please select at least one qualification.");
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
            router.push("/dashboard");
        } catch (err: unknown) {
            if (axios.isAxiosError(err)) {
                const detail = err.response?.data?.detail;
                setError(typeof detail === "string" ? detail : "Failed to create profile.");
            }
            console.error("Error creating teacher profile:", err);
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-black px-4 text-white py-12">
            <div className="w-full max-w-xl bg-zinc-950 border border-zinc-800 p-8 rounded-3xl shadow-2xl">
                <span className="text-xs font-semibold text-indigo-400 uppercase tracking-widest">Step 2 of 2</span>
                <h1 className="text-2xl font-bold mt-1 mb-1">Complete your Teacher profile</h1>
                <p className="text-zinc-400 text-sm mb-6">Tell us about your professional background.</p>

                {error && (
                    <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm p-3 rounded-lg mb-4">{error}</div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Basic Info Section */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-sm font-medium text-zinc-300 block mb-1.5">Department</label>
                            <input
                                value={form.department}
                                onChange={(e) => setForm((p) => ({ ...p, department: e.target.value }))}
                                placeholder="e.g. Mathematics"
                                required
                                className={INPUT_CLS}
                            />
                        </div>
                        <div>
                            <label className="text-sm font-medium text-zinc-300 block mb-1.5">Years of Experience</label>
                            <input
                                type="number" min="0"
                                value={form.experience}
                                onChange={(e) => setForm((p) => ({ ...p, experience: e.target.value }))}
                                required
                                className={INPUT_CLS}
                            />
                        </div>
                    </div>

                    <hr className="border-zinc-800" />

                    {/* Qualifications Multi-Select */}
                    <div>
                        <label className="text-sm font-medium text-zinc-300 block mb-2">Qualifications & Degrees</label>
                        <div className="flex flex-wrap gap-2">
                            {availableQualifications.length > 0 ? availableQualifications.map((qual) => (
                                <button
                                    key={qual}
                                    type="button"
                                    onClick={() => toggleSelection("qualifications", qual)}
                                    className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 border ${form.qualifications.includes(qual)
                                        ? "bg-indigo-600/20 text-indigo-400 border-indigo-500/50"
                                        : "bg-zinc-900 text-zinc-400 border-zinc-800 hover:bg-zinc-800 hover:text-zinc-200"
                                        }`}
                                >
                                    {qual}
                                </button>
                            )) : (
                                <p className="text-sm text-zinc-500 italic">Loading qualifications...</p>
                            )}
                        </div>
                    </div>

                    {/* Subjects Multi-Select */}
                    <div>
                        <label className="text-sm font-medium text-zinc-300 block mb-2">Teaching Subjects</label>
                        <div className="flex flex-wrap gap-2">
                            {availableSubjects.length > 0 ? availableSubjects.map((sub) => (
                                <button
                                    key={sub}
                                    type="button"
                                    onClick={() => toggleSelection("subjects", sub)}
                                    className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 border ${form.subjects.includes(sub)
                                        ? "bg-indigo-600/20 text-indigo-400 border-indigo-500/50"
                                        : "bg-zinc-900 text-zinc-400 border-zinc-800 hover:bg-zinc-800 hover:text-zinc-200"
                                        }`}
                                >
                                    {sub}
                                </button>
                            )) : (
                                <p className="text-sm text-zinc-500 italic">Loading subjects...</p>
                            )}
                        </div>
                    </div>

                    <button type="submit" disabled={saving}
                        className="w-full bg-indigo-600 text-white py-3.5 rounded-xl font-semibold hover:bg-indigo-500 transition-all disabled:opacity-50 mt-4 shadow-lg shadow-indigo-600/20">
                        {saving ? "Setting up…" : "Complete Setup →"}
                    </button>
                </form>
            </div>
        </div>
    );
}