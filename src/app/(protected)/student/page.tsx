"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { api } from "@/lib/axios";
import { Save } from "lucide-react";

const INPUT_CLS = "w-full bg-zinc-900 border border-zinc-800 text-white rounded-xl py-2.5 px-4 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all disabled:opacity-50";

export default function ProfileStudentPage() {
    const router = useRouter();
    const [form, setForm] = useState({
        rollNo: "", dob: "", parentName: "", parentEmail: ""
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(null);

    useEffect(() => {
        api.get("/api/v1/students/me")
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
                setMessage({ text: typeof detail === "string" ? detail : "Update failed.", ok: false });
            }
        } finally {
            setSaving(false);
        }
    };

    if (loading) return (
        <div className="min-h-screen flex items-center justify-center bg-black">
            <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        </div>
    );

    return (
        <div className="min-h-screen bg-black text-white p-6">
            <div className="max-w-2xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold">Student Profile</h1>
                    <p className="text-zinc-400 mt-1 text-sm">Update your student-specific details.</p>
                </div>

                {message && (
                    <div className={`p-3 rounded-xl mb-5 text-sm text-center border ${message.ok
                        ? "bg-green-500/10 text-green-400 border-green-500/20"
                        : "bg-red-500/10 text-red-400 border-red-500/20"}`}>
                        {message.text}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="bg-zinc-950 border border-zinc-800 rounded-2xl p-6 space-y-4">
                    <div>
                        <label className="text-sm text-zinc-400 block mb-1">Roll Number</label>
                        <input value={form.rollNo} onChange={(e) => setForm(p => ({ ...p, rollNo: e.target.value }))} required className={INPUT_CLS} />
                    </div>
                    <div>
                        <label className="text-sm text-zinc-400 block mb-1">Date of Birth</label>
                        <input type="date" value={form.dob} onChange={(e) => setForm(p => ({ ...p, dob: e.target.value }))} required className={INPUT_CLS} />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-sm text-zinc-400 block mb-1">Parent Name</label>
                            <input value={form.parentName} onChange={(e) => setForm(p => ({ ...p, parentName: e.target.value }))} className={INPUT_CLS} />
                        </div>
                        <div>
                            <label className="text-sm text-zinc-400 block mb-1">Parent Email</label>
                            <input type="email" value={form.parentEmail} onChange={(e) => setForm(p => ({ ...p, parentEmail: e.target.value }))} className={INPUT_CLS} />
                        </div>
                    </div>
                    <div className="flex gap-3 pt-2">
                        <button type="submit" disabled={saving}
                            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 rounded-xl font-semibold transition-all disabled:opacity-50">
                            <Save className="w-4 h-4" />
                            {saving ? "Saving…" : "Save Changes"}
                        </button>
                        <a href="/profile" className="flex items-center px-5 py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl text-sm font-medium transition-all">
                            ← Account Settings
                        </a>
                    </div>
                </form>
            </div>
        </div>
    );
}
