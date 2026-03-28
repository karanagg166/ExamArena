"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAxiosError } from "axios"; // ← only import what we need
import { api } from "@/lib/axios";
import { Save } from "lucide-react";
import { User } from "@/types/user";

// All user fields except id and role
type UserForm = Omit<User, "id" | "role">;

const INPUT_CLS = "w-full bg-zinc-900 border border-zinc-800 text-white rounded-xl py-2.5 px-4 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all disabled:opacity-50";

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
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(null);

    useEffect(() => {
        api.get("/api/v1/auth/me")
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
        setForm((p) => ({ ...p, [name]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        setMessage(null);
        try {
            await api.put("/api/v1/auth/me", form);
            setMessage({ text: "Profile updated successfully!", ok: true });
        } catch (err: unknown) {
            if (isAxiosError(err)) {
                const detail = err.response?.data?.detail;
                setMessage({ text: typeof detail === "string" ? detail : "Failed to update.", ok: false });
            }
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-black">
                <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-black text-white p-6">
            <div className="max-w-2xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold">Account Settings</h1>
                    <p className="text-zinc-400 mt-1 text-sm">Update your personal information.</p>
                </div>

                {message && (
                    <div className={`p-3 rounded-xl mb-6 text-sm text-center border ${message.ok
                        ? "bg-green-500/10 text-green-400 border-green-500/20"
                        : "bg-red-500/10 text-red-400 border-red-500/20"}`}>
                        {message.text}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="bg-zinc-950 border border-zinc-800 rounded-2xl p-6 space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-sm text-zinc-400 block mb-1">Full Name</label>
                            <input name="name" value={form.name} onChange={handleChange} required className={INPUT_CLS} />
                        </div>
                        <div>
                            <label className="text-sm text-zinc-400 block mb-1">Email</label>
                            <input type="email" name="email" value={form.email} onChange={handleChange} required className={INPUT_CLS} />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-sm text-zinc-400 block mb-1">Phone Number</label>
                            <input name="phoneNo" value={form.phoneNo} onChange={handleChange} className={INPUT_CLS} />
                        </div>
                        <div>
                            <label className="text-sm text-zinc-400 block mb-1">Date of Birth</label>
                            <input type="date" name="dateOfBirth" value={form.dateOfBirth} onChange={handleChange} className={INPUT_CLS} />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-sm text-zinc-400 block mb-1">City</label>
                            <input name="city" value={form.city} onChange={handleChange} className={INPUT_CLS} />
                        </div>
                        <div>
                            <label className="text-sm text-zinc-400 block mb-1">Pincode</label>
                            <input name="pincode" value={form.pincode} onChange={handleChange} className={INPUT_CLS} />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-sm text-zinc-400 block mb-1">State</label>
                            <input name="state" value={form.state} onChange={handleChange} className={INPUT_CLS} />
                        </div>
                        <div>
                            <label className="text-sm text-zinc-400 block mb-1">Country</label>
                            <input name="country" value={form.country} onChange={handleChange} className={INPUT_CLS} />
                        </div>
                    </div>

                    <div className="flex gap-3 pt-2">
                        <button type="submit" disabled={saving}
                            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 rounded-xl font-semibold transition-all disabled:opacity-50">
                            <Save className="w-4 h-4" />
                            {saving ? "Saving…" : "Save Changes"}
                        </button>
                        {role && (
                            <a href={`/${role.toLowerCase()}/profile`}
                                className="flex items-center px-6 py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl font-semibold transition-all text-sm">
                                Edit {role.charAt(0) + role.slice(1).toLowerCase()} Info →
                            </a>
                        )}
                    </div>
                </form>
            </div>
        </div>
    );
}