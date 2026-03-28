"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/axios";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/loading";

type User = { name: string; role: string };

const ROLE_LINKS: Record<string, { label: string; href: string }> = {
    STUDENT: { label: "Student Profile", href: "/student" },
    TEACHER: { label: "Teacher Profile", href: "/teacher" },
    PRINCIPAL: { label: "Principal Profile", href: "/principal" },
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
        <div className="flex min-h-screen items-center justify-center">
            <Spinner className="h-8 w-8 border-4" />
        </div>
    );

    const roleInfo = ROLE_LINKS[user?.role ?? ""];

    return (
        <div className="page-shell text-white">
            <div className="mx-auto max-w-4xl">
                <div className="mb-10">
                    <p className="text-sm text-zinc-400">Welcome back</p>
                    <h1 className="mt-1 text-4xl font-bold">{user?.name} 👋</h1>
                    <Badge className="mt-3 uppercase tracking-widest">{user?.role}</Badge>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <a href="/profile" className="group block">
                        <Card className="h-full border-zinc-800 transition-colors group-hover:border-zinc-600">
                            <CardHeader className="pb-3">
                                <CardDescription>Account</CardDescription>
                                <CardTitle className="text-lg transition-colors group-hover:text-indigo-300">Account Settings →</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-xs text-zinc-500">Name, email, phone, address</p>
                            </CardContent>
                        </Card>
                    </a>

                    {roleInfo && (
                        <a href={roleInfo.href} className="group block">
                            <Card className="h-full border-zinc-800 transition-colors group-hover:border-zinc-600">
                                <CardHeader className="pb-3">
                                    <CardDescription>Profile</CardDescription>
                                    <CardTitle className="text-lg transition-colors group-hover:text-indigo-300">{roleInfo.label} →</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-xs text-zinc-500">Role-specific information</p>
                                </CardContent>
                            </Card>
                        </a>
                    )}
                </div>
            </div>
        </div>
    );
}
