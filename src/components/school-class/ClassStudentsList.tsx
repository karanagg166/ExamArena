"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/axios";
import type { AxiosError } from "axios";
import type { StudentProfileResponse } from "@/types/student";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/loading";
import { Users, Mail, Phone, MapPin } from "lucide-react";

export function ClassStudentsList({ classId }: { classId: string }) {
  const [students, setStudents] = useState<StudentProfileResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStudents = async () => {
      setLoading(true);
      setError(null);
      try {
        const { data } = await api.get<StudentProfileResponse[]>(
          `/api/v1/classes/${classId}/students`,
        );
        setStudents(data);
      } catch (err: unknown) {
        const axiosError = err as AxiosError<{ detail?: string }>;
        setError(
          axiosError.response?.data?.detail ??
            (err instanceof Error ? err.message : "Failed to load students."),
        );
      } finally {
        setLoading(false);
      }
    };

    if (classId) fetchStudents();
  }, [classId]);

  if (loading) {
    return (
      <div className="flex justify-center p-12">
        <Spinner className="h-8 w-8 border-4" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-500/30">
        <CardContent className="pt-6">
          <p className="text-red-400 text-center">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (!students.length) {
    return (
      <Card className="bg-zinc-900 border-zinc-800">
        <CardContent className="flex flex-col items-center justify-center p-16 text-center space-y-4">
          <div className="p-4 bg-zinc-800 rounded-full">
            <Users className="w-8 h-8 text-zinc-400" />
          </div>
          <div>
            <h3 className="text-lg font-medium text-white mb-1">
              No Students Found
            </h3>
            <p className="text-zinc-500 max-w-sm">
              There are currently no students assigned to this class. Students
              will appear here once they are registered to this class ID.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Users className="w-6 h-6 text-indigo-400" />
          Class Roster ({students.length})
        </h2>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {students.map((student) => (
          <Card
            key={student.id}
            className="bg-zinc-900 border-zinc-800 hover:border-zinc-700 transition-colors"
          >
            <CardHeader className="pb-3 border-b border-zinc-800/50">
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg text-white mb-1">
                    {student.user?.name ?? "Unknown Student"}
                  </CardTitle>
                  <p className="text-xs font-mono text-indigo-400 bg-indigo-500/10 inline-block px-2 py-1 rounded">
                    Roll: {student.rollNo}
                  </p>
                </div>
              </div>
            </CardHeader>

            <CardContent className="pt-4 space-y-3">
              <div className="grid gap-2 text-sm text-zinc-400">
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4 text-zinc-500" />
                  <span className="truncate">
                    {student.user?.email ?? "No email"}
                  </span>
                </div>
                {student.user?.phoneNo && (
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-zinc-500" />
                    <span>{student.user.phoneNo}</span>
                  </div>
                )}
                {student.user?.city && (
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-zinc-500" />
                    <span>
                      {student.user.city}, {student.user.state}
                    </span>
                  </div>
                )}
              </div>

              <div className="pt-3 border-t border-zinc-800/50 space-y-1">
                <p className="text-xs text-zinc-500 uppercase tracking-wider font-semibold">
                  Guardian Info
                </p>
                <p className="text-sm text-zinc-300">{student.parentName}</p>
                <p className="text-xs text-zinc-400 truncate">
                  {student.parentEmail}
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
