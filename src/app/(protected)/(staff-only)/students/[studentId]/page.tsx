"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/axios";
import type { StudentProfileResponse } from "@/types/student";
import { Spinner } from "@/components/ui/loading";
import StudentProfileCard from "@/components/student/StudentProfileCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

export default function StudentPage() {
  const { studentId } = useParams<{ studentId: string }>();
  const router = useRouter();
  const [student, setStudent] = useState<StudentProfileResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStudent = async () => {
      setLoading(true);
      setError(null);
      try {
        const { data } = await api.get<StudentProfileResponse>(
          `/api/v1/students/${studentId}`,
        );
        setStudent(data);
      } catch (err: unknown) {
        setError(
          (err as { response?: { data?: { detail?: string } } })?.response?.data
            ?.detail ??
            (err instanceof Error ? err.message : "Something went wrong"),
        );
      } finally {
        setLoading(false);
      }
    };

    if (studentId) fetchStudent();
  }, [studentId]);

  if (loading) {
    return (
      <div className="flex min-h-[80vh] items-center justify-center">
        <Spinner className="h-10 w-10 border-4" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[80vh] items-center justify-center p-8">
        <Card className="max-w-md w-full border-red-500/30">
          <CardHeader>
            <CardTitle className="text-red-500">
              ⚠️ Unable to load profile
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-600 dark:text-slate-300">
              {error}
            </p>
            <Button
              variant="outline"
              onClick={() => router.back()}
              className="w-full"
            >
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!student) return null;

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-4xl mx-auto mb-6">
        <Button
          variant="ghost"
          onClick={() => router.back()}
          className="flex items-center gap-2 -ml-4 text-slate-500 hover:text-slate-900 dark:hover:text-slate-100"
        >
          <ArrowLeft size={16} />
          Back
        </Button>
      </div>
      <StudentProfileCard student={student} />
    </div>
  );
}
