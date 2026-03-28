'use client';
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/axios";
import type { SchoolClass } from "@/types/index";
import SchoolClassCard from "@/components/school-class/SchoolClassCard";
import { Spinner } from "@/components/ui/loading";

export default function SchoolClassesPage() {
    const { schoolId } = useParams<{ schoolId: string }>();
    const [classes, setClasses] = useState<SchoolClass[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchClasses = async () => {
            setLoading(true);
            setError(null);
            try {
                const { data } = await api.get<SchoolClass[]>(`/api/v1/schools/${schoolId}/classes`);
                setClasses(data);
            } catch (err: unknown) {
                setError((err as { message?: string })?.message ?? "Something went wrong");
            } finally {
                setLoading(false);
            }
        };

        if (schoolId) fetchClasses();
    }, [schoolId]);

    if (loading) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <Spinner className="h-8 w-8 border-4" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="page-shell text-white">
                <div className="max-w-2xl bg-red-500/10 border border-red-500/30 rounded-2xl px-5 py-4">
                    <p className="text-red-300 font-medium">Unable to load classes</p>
                    <p className="text-red-200 text-sm mt-1">{error}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="page-shell text-white">

            {/* Header */}
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Classes</h1>
                    <p className="text-sm text-zinc-400 mt-0.5">
                        {classes.length} class{classes.length !== 1 ? "es" : ""} found
                    </p>
                </div>
            </div>

            {/* Empty state */}
            {classes.length === 0 && (
                <div className="text-center py-20 text-zinc-500">
                    <p className="text-4xl mb-3">🏫</p>
                    <p className="text-lg font-medium text-zinc-400">No classes found</p>
                    <p className="text-sm mt-1">This school has no classes yet</p>
                </div>
            )}

            {/* Grid */}
            {classes.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                    {classes.map((schoolClass) => (
                        <SchoolClassCard key={schoolClass.id} schoolClass={schoolClass} />
                    ))}
                </div>
            )}

        </div>
    );
}