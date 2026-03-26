"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { api } from "@/lib/axios";
import { Save } from "lucide-react";

const INPUT_CLS = "w-full bg-zinc-900 border border-zinc-800 text-white rounded-xl py-2.5 px-4 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all disabled:opacity-50";

export default function ProfilePrincipalPage() {
    const router = useRouter();
    const [form, setForm] = useState({ experience: 0 });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(null);

    useEffect(() => {
        api.get("/api/v1/principals/me")
            .then((r) => setForm({ experience: r.data.experience ?? 0 }))
            .catch(() => router.push("/login"))
            .finally(() => setLoading(false));
    }, [router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        setMessage(null);
        try {
            await api.put("/api/v1/principals/me", { experience: form.experience });
            setMessage({ text: "Principal profile updated!", ok: true });
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
                    <h1 className="text-3xl font-bold">Principal Profile</h1>
                    <p className="text-zinc-400 mt-1 text-sm">Update your principal details.</p>
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
                        <label className="text-sm text-zinc-400 block mb-1">Years of Experience</label>
                        <input
                            type="number" min="0"
                            value={form.experience}
                            onChange={(e) => setForm({ experience: parseInt(e.target.value) || 0 })}
                            className={INPUT_CLS}
                        />
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
