"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/axios";

type User = { name: string; role: string };

const ROLE_LINKS: Record<string, { label: string; href: string; color: string }> = {
    STUDENT: { label: "Student Profile", href: "/student", color: "bg-sky-600 hover:bg-sky-500" },
    TEACHER: { label: "Teacher Profile", href: "/teacher", color: "bg-emerald-600 hover:bg-emerald-500" },
    PRINCIPAL: { label: "Principal Profile", href: "/principal", color: "bg-violet-600 hover:bg-violet-500" },
};

export default function DashboardPage() {
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get("/api/v1/auth/me")
            .then((r) => setUser(r.data))
            .catch(() => router.push("/login"))
            .finally(() => setLoading(false));
    }, [router]);

    if (loading) return (
        <div className="min-h-screen flex items-center justify-center bg-black">
            <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        </div>
    );

    const roleInfo = ROLE_LINKS[user?.role ?? ""];

    return (
        <div className="min-h-screen bg-black text-white p-6">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-10">
                    <p className="text-zinc-400 text-sm">Welcome back</p>
                    <h1 className="text-4xl font-bold mt-1">{user?.name} 👋</h1>
                    <span className="inline-block mt-2 text-xs font-semibold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1 rounded-full uppercase tracking-widest">
                        {user?.role}
                    </span>
                </div>

                {/* Quick Links */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <a href="/profile"
                        className="block bg-zinc-950 border border-zinc-800 hover:border-zinc-600 rounded-2xl p-5 transition-all group">
                        <div className="text-zinc-400 text-sm mb-1">Account</div>
                        <div className="text-lg font-semibold group-hover:text-indigo-400 transition-colors">Account Settings →</div>
                        <div className="text-zinc-500 text-xs mt-1">Name, email, phone, address</div>
                    </a>

                    {roleInfo && (
                        <a href={roleInfo.href}
                            className="block bg-zinc-950 border border-zinc-800 hover:border-zinc-600 rounded-2xl p-5 transition-all group">
                            <div className="text-zinc-400 text-sm mb-1">Profile</div>
                            <div className="text-lg font-semibold group-hover:text-indigo-400 transition-colors">{roleInfo.label} →</div>
                            <div className="text-zinc-500 text-xs mt-1">Role-specific information</div>
                        </a>
                    )}
                </div>
            </div>
        </div>
    );
}
