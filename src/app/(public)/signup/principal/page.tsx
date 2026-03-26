"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/axios";
import { isAxiosError } from "axios";

type TeacherStatus = "loading" | "exists" | "not_found";

export default function SignupPrincipalPage() {
    const router = useRouter();
    const [status, setStatus] = useState<TeacherStatus>("loading");

    useEffect(() => {
        api.get("/api/v1/teachers/me")
            .then(() => setStatus("exists"))
            .catch((err) => {
                if (isAxiosError(err) && err.response?.status === 404) {
                    setStatus("not_found");
                }
            });
    }, []);

    if (status === "loading") {
        return (
            <div className="min-h-screen flex items-center justify-center bg-black">
                <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    // ❌ No teacher profile — block them
    if (status === "not_found") {
        return (
            <div className="min-h-screen flex items-center justify-center bg-black px-4 text-white py-12">
                <div className="w-full max-w-xl bg-zinc-950 border border-zinc-800 p-8 rounded-3xl shadow-2xl text-center">
                    <span className="text-xs font-semibold text-red-400 uppercase tracking-widest">Step 2 of 2</span>
                    <h1 className="text-2xl font-bold mt-2 mb-2">Principal Account</h1>

                    <div className="bg-red-500/10 border border-red-500/20 text-red-300 p-5 rounded-xl text-sm text-left space-y-2 mb-6">
                        <p className="font-semibold text-red-400">Teacher Profile Required</p>
                        <p className="text-red-300/90">
                            You must have a Teacher profile before becoming a Principal.
                            Please complete your Teacher registration first.
                        </p>
                    </div>

                    <button
                        onClick={() => router.push("/signup/teacher")}
                        className="w-full bg-indigo-600 hover:bg-indigo-500 text-white py-3 rounded-xl font-semibold transition-all shadow-lg shadow-indigo-600/20"
                    >
                        Create Teacher Profile First →
                    </button>
                </div>
            </div>
        );
    }

    // ✅ Has teacher profile — show school options
    return (
        <div className="min-h-screen flex items-center justify-center bg-black px-4 text-white py-12">
            <div className="w-full max-w-xl bg-zinc-950 border border-zinc-800 p-8 rounded-3xl shadow-2xl text-center">
                <span className="text-xs font-semibold text-indigo-400 uppercase tracking-widest">Step 2 of 2</span>
                <h1 className="text-2xl font-bold mt-2 mb-2">Principal Account</h1>
                <p className="text-zinc-400 text-sm mb-8">
                    You are all set! Now choose how you want to proceed.
                </p>

                <div className="grid grid-cols-1 gap-4">
                    {/* Option 1 — Create a new school */}
                    <button
                        onClick={() => router.push("/school/profile")}
                        className="w-full bg-indigo-600 hover:bg-indigo-500 text-white py-5 px-6 rounded-2xl font-semibold transition-all shadow-lg shadow-indigo-600/20 text-left flex items-start gap-4"
                    >
                        <span className="text-2xl">🏫</span>
                        <div>
                            <p className="font-bold text-base">Create a New School</p>
                            <p className="text-indigo-200/70 text-sm font-normal mt-0.5">
                                Register a new school and become its principal.
                            </p>
                        </div>
                    </button>

                    {/* Option 2 — Join an existing school */}
                    <button
                        onClick={() => router.push("/principal/school/join")}
                        className="w-full bg-zinc-800 hover:bg-zinc-700 text-white py-5 px-6 rounded-2xl font-semibold transition-all text-left flex items-start gap-4"
                    >
                        <span className="text-2xl">🔑</span>
                        <div>
                            <p className="font-bold text-base">Join an Existing School</p>
                            <p className="text-zinc-400 text-sm font-normal mt-0.5">
                                Use a school code to join as principal.
                            </p>
                        </div>
                    </button>
                </div>
            </div>
        </div>
    );
}
