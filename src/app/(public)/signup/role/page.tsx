"use client";
// Redirect shim — this page is replaced by /signup/student, /signup/teacher, /signup/principal
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/axios";

export default function SignupRoleRedirect() {
    const router = useRouter();
    useEffect(() => {
        api.get("/api/v1/auth/me")
            .then((r) => router.replace(`/signup/${(r.data.role as string).toLowerCase()}`))
            .catch(() => router.replace("/login"));
    }, [router]);
    return (
        <div className="min-h-screen flex items-center justify-center bg-black">
            <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        </div>
    );
}
