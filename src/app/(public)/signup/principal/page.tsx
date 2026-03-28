"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/axios";
import { isAxiosError } from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/loading";

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
            <div className="flex min-h-screen items-center justify-center">
                <Spinner className="h-8 w-8 border-4" />
            </div>
        );
    }

    // ❌ No teacher profile — block them
    if (status === "not_found") {
        return (
            <div className="page-shell flex min-h-screen items-center justify-center text-white">
                <Card className="w-full max-w-xl shadow-2xl shadow-indigo-950/20">
                    <CardHeader className="text-center">
                        <Badge variant="danger" className="mx-auto uppercase tracking-widest">Step 2 of 2</Badge>
                        <CardTitle className="mt-2 text-2xl">Principal Account</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="mb-6 space-y-2 rounded-xl border border-red-500/20 bg-red-500/10 p-5 text-left text-sm text-red-200">
                            <p className="font-semibold text-red-300">Teacher Profile Required</p>
                            <p>
                                You must have a Teacher profile before becoming a Principal.
                                Please complete your Teacher registration first.
                            </p>
                        </div>

                        <Button
                            onClick={() => {
                                toast.info("Redirecting to teacher setup");
                                router.push("/signup/teacher");
                            }}
                            className="w-full"
                        >
                            Create Teacher Profile First
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // ✅ Has teacher profile — show school options
    return (
        <div className="page-shell flex min-h-screen items-center justify-center text-white">
            <Card className="w-full max-w-xl shadow-2xl shadow-indigo-950/20">
                <CardHeader className="text-center">
                    <Badge className="mx-auto uppercase tracking-widest">Step 2 of 2</Badge>
                    <CardTitle className="mt-2 text-2xl">Principal Account</CardTitle>
                    <CardDescription>You are all set! Choose how you want to proceed.</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 gap-4">
                        <Button
                            variant="primary"
                            className="h-auto justify-start gap-4 px-6 py-5 text-left"
                            onClick={() => {
                                toast.success("Starting school creation");
                                router.push("/school/profile");
                            }}
                        >
                            <span className="text-2xl">🏫</span>
                            <span>
                                <span className="block text-base font-bold">Create a New School</span>
                                <span className="text-sm font-normal text-indigo-100/80">Register a new school and become its principal.</span>
                            </span>
                        </Button>

                        <Button
                            variant="secondary"
                            className="h-auto justify-start gap-4 px-6 py-5 text-left"
                            onClick={() => {
                                toast.info("Opening school join flow");
                                router.push("/principal/school/join");
                            }}
                        >
                            <span className="text-2xl">🔑</span>
                            <span>
                                <span className="block text-base font-bold">Join an Existing School</span>
                                <span className="text-sm font-normal text-zinc-400">Use a school code to join as principal.</span>
                            </span>
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
