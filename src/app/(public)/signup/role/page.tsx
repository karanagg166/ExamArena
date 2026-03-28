"use client";
// Redirect shim — this page is replaced by /signup/student, /signup/teacher, /signup/principal
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/axios";
import { Spinner } from "@/components/ui/loading";

export default function SignupRoleRedirect() {
    const router = useRouter();
    useEffect(() => {
        api.get("/api/v1/auth/me")
            .then((r) => router.replace(`/signup/${(r.data.role as string).toLowerCase()}`))
            .catch(() => router.replace("/login"));
    }, [router]);
    return (
        <div className="flex min-h-screen items-center justify-center">
            <Spinner className="h-8 w-8 border-4" />
        </div>
    );
}
