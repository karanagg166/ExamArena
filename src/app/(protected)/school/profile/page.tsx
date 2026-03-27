"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/axios";
import axios from "axios";

const initialForm = {
    name: "",
    address: "",
    city: "",
    state: "",
    country: "",
    pincode: "",
    schoolCode: "",
};

const SchoolProfile = () => {
    const router = useRouter();
    const [form, setForm] = useState(initialForm);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ text: string; type: string }>({ text: "", type: "" });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setForm((prev) => ({
            ...prev,
            [name]: value,
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        setMessage({ text: "", type: "" });

        try {
            const response = await api.post("/api/v1/schools/", form);

            if (response.status === 200 || response.status === 201) {
                setMessage({ text: "School created successfully!", type: "success" });
                setForm(initialForm);
                router.push("/principal");
            }
        } catch (err: unknown) {
            if (axios.isAxiosError(err)) {
                const detail = err.response?.data?.detail;
                const text = Array.isArray(detail)
                    ? detail.map((d: { msg: string; loc: string[] }) => `${d.loc?.slice(-1)[0]}: ${d.msg}`).join(", ")
                    : (typeof detail === "string" ? detail : "Failed to create school.");
                setMessage({ text, type: "error" });
            } else {
                setMessage({ text: "An unexpected error occurred.", type: "error" });
            }
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-black px-4 text-white py-12">
            <div className="w-full max-w-2xl bg-zinc-950 border border-zinc-800 p-8 rounded-3xl shadow-2xl">
                <h1 className="text-3xl font-bold mb-2">Create School</h1>
                <p className="text-zinc-400 mb-6 text-sm">
                    Fill in the details below to register your institution.
                </p>

                {message.text && (
                    <div className={`p-3 rounded-xl mb-6 text-sm text-center ${message.type === "error" ? "bg-red-500/10 text-red-400 border border-red-500/20" : "bg-green-500/10 text-green-400 border border-green-500/20"}`}>
                        {message.text}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label className="text-sm font-medium text-zinc-300 ml-1 block mb-1.5">School Name</label>
                        <input
                            name="name"
                            value={form.name}
                            onChange={handleChange}
                            className="w-full bg-zinc-900 border border-zinc-800 text-white rounded-xl py-3 px-4 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
                            required
                        />
                    </div>

                    <div>
                        <label className="text-sm font-medium text-zinc-300 ml-1 block mb-1.5">Address</label>
                        <input
                            name="address"
                            value={form.address}
                            onChange={handleChange}
                            className="w-full bg-zinc-900 border border-zinc-800 text-white rounded-xl py-3 px-4 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
                            required
                        />
                    </div>

                    <div>
                        <label className="text-sm font-medium text-zinc-300 ml-1 block mb-1.5">School Code</label>
                        <input
                            name="schoolCode"
                            value={form.schoolCode}
                            onChange={handleChange}
                            className="w-full bg-zinc-900 border border-zinc-800 text-white rounded-xl py-3 px-4 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
                            required
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-sm font-medium text-zinc-300 ml-1 block mb-1.5">City</label>
                            <input
                                name="city"
                                value={form.city}
                                onChange={handleChange}
                                className="w-full bg-zinc-900 border border-zinc-800 text-white rounded-xl py-3 px-4 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
                                required
                            />
                        </div>
                        <div>
                            <label className="text-sm font-medium text-zinc-300 ml-1 block mb-1.5">Pincode</label>
                            <input
                                name="pincode"
                                value={form.pincode}
                                onChange={handleChange}
                                className="w-full bg-zinc-900 border border-zinc-800 text-white rounded-xl py-3 px-4 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
                                required
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-sm font-medium text-zinc-300 ml-1 block mb-1.5">State</label>
                            <input
                                name="state"
                                value={form.state}
                                onChange={handleChange}
                                className="w-full bg-zinc-900 border border-zinc-800 text-white rounded-xl py-3 px-4 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
                                required
                            />
                        </div>
                        <div>
                            <label className="text-sm font-medium text-zinc-300 ml-1 block mb-1.5">Country</label>
                            <input
                                name="country"
                                value={form.country}
                                onChange={handleChange}
                                className="w-full bg-zinc-900 border border-zinc-800 text-white rounded-xl py-3 px-4 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
                                required
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={saving}
                        className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3.5 px-4 rounded-xl transition-all active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed mt-4 shadow-lg shadow-indigo-600/20"
                    >
                        {saving ? "Creating School..." : "Create School"}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default SchoolProfile;