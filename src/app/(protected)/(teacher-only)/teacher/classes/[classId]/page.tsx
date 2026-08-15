"use client";
import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/loading";
import { Button } from "@/components/ui/button";
import { useSchoolClassStore } from "@/stores";
import { ArrowLeft, Copy, ListChecks, Trash2 } from "lucide-react";
import { toast } from "sonner";

export default function ClassPage() {
  const { classId } = useParams<{ classId: string }>();
  const router = useRouter();
  const { classes, loading, error, fetchClass, deleteClass } = useSchoolClassStore();

  const schoolClass = classes.find((c) => c.id === classId);
  useEffect(() => {
    if (classId && !schoolClass) {
      fetchClass(classId);
    }
  }, [classId, fetchClass, schoolClass]);

  const handleDelete = async () => {
    if (!schoolClass) return;
    if (window.confirm(`Are you sure you want to delete class '${schoolClass.name}'?`)) {
      const success = await deleteClass(schoolClass.id);
      if (success) {
        toast.success(`Class '${schoolClass.name}' deleted successfully`);
        router.push("/teacher/classes");
      } else {
        toast.error("Failed to delete class");
      }
    }
  };

  const copyJoinCode = async () => {
    if (!schoolClass) return;
    try {
      await navigator.clipboard.writeText(schoolClass.joinCode);
      toast.success("Join code copied to clipboard");
    } catch {
      toast.error("Unable to copy the join code");
    }
  };

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
        <Card className="max-w-2xl border-red-500/30">
          <CardHeader>
            <CardTitle className="text-red-300">Unable to load class</CardTitle>
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
      <div className="max-w-3xl mb-6">
        <Button
          variant="ghost"
          className="text-zinc-400 hover:text-white"
          onClick={() => router.back()}
        >
          <ArrowLeft className="w-4 h-4 mr-2" /> Back
        </Button>
      </div>
      <Card className="max-w-3xl space-y-6">
        {/* Header */}
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-2xl">{schoolClass.name}</CardTitle>
            {schoolClass.schoolName && (
              <p className="text-sm text-zinc-400 mt-1">
                {schoolClass.schoolName}
              </p>
            )}
          </div>
          <Button variant="destructive" size="sm" onClick={handleDelete}>
            <Trash2 className="w-4 h-4 mr-2" /> Delete Class
          </Button>
        </CardHeader>

        <CardContent className="space-y-6">
          <div className="rounded-xl border border-indigo-400/25 bg-indigo-500/5 p-4">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-300">Student enrollment code</p>
                <p className="mt-1 font-mono text-2xl font-bold tracking-[0.2em] text-white">{schoolClass.joinCode}</p>
                <p className="mt-1 text-sm text-zinc-400">Share this code with students; requests require your approval.</p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={copyJoinCode}>
                  <Copy className="mr-2 h-4 w-4" /> Copy
                </Button>
                <Button size="sm" onClick={() => router.push(`/teacher/classes/${classId}/requests`)}>
                  <ListChecks className="mr-2 h-4 w-4" /> Requests
                </Button>
              </div>
            </div>
          </div>

          {/* Basic Info */}
          <div className="grid gap-2 text-sm text-zinc-300 sm:grid-cols-2">
            <p>
              <span className="text-zinc-500">Class Name:</span> {schoolClass.name}
            </p>
            <p>
              <span className="text-zinc-500">School:</span>{" "}
              {schoolClass.schoolName || "My School"}
            </p>
            <p>
              <span className="text-zinc-500">Created:</span>{" "}
              {new Date(schoolClass.createdAt).toLocaleDateString()}
            </p>
            <p>
              <span className="text-zinc-500">Updated:</span>{" "}
              {new Date(schoolClass.updatedAt).toLocaleDateString()}
            </p>
          </div>

          {/* Teachers */}
          {schoolClass.teachers && schoolClass.teachers.length > 0 && (
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
                      {teacher.department}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* No teachers fallback */}
          {(!schoolClass.teachers || schoolClass.teachers.length === 0) && (
            <p className="text-sm text-zinc-500">
              No teachers assigned to this class.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
