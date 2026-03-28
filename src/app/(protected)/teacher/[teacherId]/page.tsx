'use client';

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/axios";
import { TeacherProfileResponse } from "@/types/teacher";
import { Spinner } from "@/components/ui/loading";
import TeacherProfileCard from "@/components/teacher/TeacherProfileCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

export default function TeacherPage() {
    const { teacherId } = useParams<{ teacherId: string }>();
    const router = useRouter();
    const [teacher, setTeacher] = useState<TeacherProfileResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchTeacher = async () => {
            setLoading(true);
            setError(null);
            try {
                const { data } = await api.get<TeacherProfileResponse>(`/api/v1/teachers/${teacherId}`);
                setTeacher(data);
            } catch (err: unknown) {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                setError((err as any)?.response?.data?.detail || (err as Error)?.message || "Something went wrong");
            } finally {
                setLoading(false);
            }
        };

        if (teacherId) fetchTeacher();
    }, [teacherId]);

    if (loading) {
        return (
            <div className="flex min-h-[80vh] items-center justify-center bg-gray-50/50 dark:bg-slate-900/50 rounded-xl m-4">
                <Spinner className="h-10 w-10 text-indigo-600 border-4" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-8 min-h-[80vh] flex items-center justify-center">
                <Card className="max-w-md w-full border-red-500/30 shadow-red-500/10 shadow-xl">
                    <CardHeader>
                        <CardTitle className="text-red-500 flex items-center gap-2">
                            <span>⚠️</span> Unable to load profile
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <p className="text-sm text-slate-600 dark:text-slate-300">{error}</p>
                        <Button variant="outline" onClick={() => router.back()} className="w-full">
                            Go Back
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    if (!teacher) return null;

    return (
        <div className="p-4 md:p-8 min-h-screen bg-transparent">
            <div className="max-w-4xl mx-auto mb-6">
                <Button 
                    variant="ghost" 
                    onClick={() => router.back()} 
                    className="text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 flex items-center gap-2 -ml-4"
                >
                    <ArrowLeft size={16} />
                    Back
                </Button>
            </div>
            <TeacherProfileCard teacher={teacher} />
        </div>
    );
}
