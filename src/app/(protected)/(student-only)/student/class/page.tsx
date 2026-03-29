"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/axios";
import type { AxiosError } from "axios";
import type { SchoolClass, StudentProfileResponse } from "@/types/index";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/loading";

export default function StudentClassPage() {
  const [schoolClass, setSchoolClass] = useState<SchoolClass | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchClass = async () => {
      setLoading(true);
      setError(null);
      try {
        const { data: student } = await api.get<StudentProfileResponse>(
          "/api/v1/students/me",
        );

        if (!student.classId) {
          setError("You are not assigned to any class yet.");
          return;
        }

        const { data: classData } = await api.get<SchoolClass>(
          `/api/v1/classes/${student.classId}`,
        );
        setSchoolClass(classData);
      } catch (err: unknown) {
        const axiosError = err as AxiosError<{ detail?: string }>;
        setError(
          axiosError.response?.data?.detail ??
            (err instanceof Error ? err.message : "Something went wrong"),
        );
      } finally {
        setLoading(false);
      }
    };

    fetchClass();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center">
        <Spinner className="h-8 w-8 border-4" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-shell text-white">
        <Card className="max-w-2xl border-red-500/30">
          <CardHeader>
            <CardTitle className="text-red-300">
              ⚠️ Unable to load class
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-red-200">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!schoolClass) return null;

  return (
    <div className="page-shell text-white">
      <Card className="max-w-3xl space-y-6">
        <CardHeader>
          <CardTitle className="text-2xl">{schoolClass.name}</CardTitle>
          {schoolClass.schoolName && (
            <p className="text-sm text-zinc-400">{schoolClass.schoolName}</p>
          )}
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Basic Info */}
          <div className="grid gap-2 text-sm text-zinc-300 sm:grid-cols-2">
            <p>
              <span className="text-zinc-500">Class ID:</span> {schoolClass.id}
            </p>
            <p>
              <span className="text-zinc-500">School ID:</span>{" "}
              {schoolClass.schoolId}
            </p>
          </div>

          {/* Teachers */}
          {schoolClass.teachers && schoolClass.teachers.length > 0 ? (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wide">
                Teachers ({schoolClass.teachers.length})
              </h3>
              <div className="grid gap-2 sm:grid-cols-2">
                {schoolClass.teachers.map((teacher) => (
                  <div
                    key={teacher.id}
                    className="rounded-lg border border-zinc-700 bg-zinc-800/50 px-4 py-3 text-sm"
                  >
                    <p className="font-medium text-zinc-200">{teacher.name}</p>
                    <p className="text-zinc-500 text-xs mt-0.5">
                      {teacher.department || "No Department"}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-zinc-500">
              No teachers assigned to this class.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
