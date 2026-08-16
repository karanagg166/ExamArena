"use client";

import { useEffect, useState, useCallback } from "react";
import { useSchoolStore, useSchoolClassStore, useTeacherRequestStore } from "@/stores";
import SchoolClassCard from "@/components/school-class/SchoolClassCard";
import { Spinner } from "@/components/ui/loading";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { ArrowLeft, Plus, UserPlus, Check, BookOpen } from "lucide-react";
import { api } from "@/lib/axios";

type TeacherItem = {
  id: string;
  name: string;
  email: string;
  department: string;
  subjects: string[];
};

export default function PrincipalSchoolClassPage() {
  const router = useRouter();
  const { school, loading: schoolLoading, fetchSchool } = useSchoolStore();
  const {
    classes,
    loading: classesLoading,
    fetchClassesBySchool,
  } = useSchoolClassStore();

  const { assignClassesToTeacher } = useTeacherRequestStore();

  // Multi-Class Assignment Modal state
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [teachers, setTeachers] = useState<TeacherItem[]>([]);
  const [selectedTeacherId, setSelectedTeacherId] = useState<string>("");
  const [selectedClassIds, setSelectedClassIds] = useState<string[]>([]);
  const [assignLoading, setAssignLoading] = useState(false);
  const [assignError, setAssignError] = useState<string | null>(null);
  const [assignSuccess, setAssignSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!school) fetchSchool();
  }, [school, fetchSchool]);

  useEffect(() => {
    if (school?.id) fetchClassesBySchool(school.id);
  }, [school?.id, fetchClassesBySchool]);

  const loadTeachers = useCallback(async () => {
    if (!school?.id) return;
    try {
      const { data } = await api.get<TeacherItem[]>("/api/v1/teachers", {
        params: { scopeSchoolId: school.id },
      });
      setTeachers(data);
      if (data.length > 0 && !selectedTeacherId) {
        setSelectedTeacherId(data[0].id);
      }
    } catch {
      // Ignored
    }
  }, [school, selectedTeacherId]);

  const handleOpenAssignModal = () => {
    setIsAssignModalOpen(true);
    setAssignError(null);
    setAssignSuccess(null);
    setSelectedClassIds([]);
    loadTeachers();
  };

  const toggleClassSelection = (classId: string) => {
    setSelectedClassIds((prev) =>
      prev.includes(classId)
        ? prev.filter((id) => id !== classId)
        : [...prev, classId]
    );
  };

  const handleAssignClasses = async () => {
    if (!selectedTeacherId) {
      setAssignError("Please select a teacher.");
      return;
    }
    if (selectedClassIds.length === 0) {
      setAssignError("Please select at least one class to assign.");
      return;
    }

    setAssignLoading(true);
    setAssignError(null);
    setAssignSuccess(null);

    const res = await assignClassesToTeacher({
      teacherId: selectedTeacherId,
      classIds: selectedClassIds,
    });

    if (res.success) {
      setAssignSuccess(res.message || "Classes successfully assigned to teacher!");
      if (school?.id) fetchClassesBySchool(school.id);
      setTimeout(() => {
        setIsAssignModalOpen(false);
      }, 1500);
    } else {
      setAssignError(res.error || "Failed to assign classes.");
    }
    setAssignLoading(false);
  };

  if (schoolLoading || classesLoading) {
    return (
      <div className="flex min-h-[80vh] items-center justify-center">
        <Spinner className="h-10 w-10 text-indigo-500 border-4" />
      </div>
    );
  }

  if (!school) {
    return (
      <div className="page-shell flex min-h-[70vh] flex-col items-center justify-center p-6 text-center">
        <div className="max-w-md rounded-2xl border border-zinc-800 bg-zinc-950/60 p-8 shadow-xl space-y-4">
          <h2 className="text-xl font-bold text-white">No School Associated</h2>
          <p className="text-sm text-zinc-400">
            You must establish or join a school before managing classes and student rosters.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
            <Button onClick={() => router.push("/signup/principal/create-school")}>
              Create School
            </Button>
            <Button variant="secondary" onClick={() => router.push("/signup/principal/join-school")}>
              Join School
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-shell text-white p-6 max-w-6xl mx-auto space-y-8">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          className="text-zinc-400 hover:text-white"
          onClick={() => router.back()}
        >
          <ArrowLeft className="w-4 h-4 mr-2" /> Back
        </Button>
      </div>

      <Card className="border-zinc-800 bg-zinc-950/50">
        <CardHeader className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div>
            <CardTitle className="text-3xl font-bold tracking-tight">
              Classes Directory
            </CardTitle>
            <CardDescription className="text-zinc-400">
              Overview of all classes in {school.name}. Click into a class to view
              its specific details, student roster, and assigned faculty.
            </CardDescription>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              onClick={handleOpenAssignModal}
              className="border-zinc-700 hover:bg-zinc-800 text-zinc-200"
            >
              <UserPlus className="mr-2 h-4 w-4 text-indigo-400" />
              Assign Classes to Faculty
            </Button>
            <Button onClick={() => router.push("/principal/school/classes/new")}>
              <Plus className="mr-2 h-4 w-4" />
              Create Class
            </Button>
          </div>
        </CardHeader>
      </Card>

      {classes.length === 0 ? (
        <div className="flex min-h-[40vh] items-center justify-center rounded-2xl border border-zinc-800 border-dashed bg-zinc-900/20">
          <p className="text-zinc-500">No classes found in this school.</p>
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {classes.map((cls) => (
            <SchoolClassCard key={cls.id} schoolClass={cls} />
          ))}
        </div>
      )}

      {/* Multi-Class Assignment Modal */}
      {isAssignModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-3xl p-6 shadow-2xl space-y-5 animate-in zoom-in-95 duration-200">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-xl font-bold text-white">
                  Assign Multiple Classes
                </h3>
                <p className="text-xs text-zinc-400 mt-1">
                  Select a faculty member and check all classes they will instruct.
                </p>
              </div>
              <button
                onClick={() => setIsAssignModalOpen(false)}
                className="text-zinc-500 hover:text-white"
              >
                ✕
              </button>
            </div>

            {assignSuccess && (
              <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/30 p-3 text-xs text-emerald-300">
                {assignSuccess}
              </div>
            )}

            {assignError && (
              <div className="rounded-xl border border-red-500/30 bg-red-950/30 p-3 text-xs text-red-300">
                {assignError}
              </div>
            )}

            {/* Select Faculty */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-zinc-300">
                Select Teacher / Faculty Member
              </label>
              {teachers.length === 0 ? (
                <div className="p-3 rounded-xl bg-zinc-800/50 border border-zinc-700 text-xs text-zinc-400">
                  No enrolled faculty members found. Approve faculty join requests first.
                </div>
              ) : (
                <select
                  value={selectedTeacherId}
                  onChange={(e) => setSelectedTeacherId(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl bg-zinc-800 border border-zinc-700 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {teachers.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name} ({t.email}) {t.department ? `- ${t.department}` : ""}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Select Classes (Multi-select) */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-zinc-300">
                  Select Classes to Assign ({selectedClassIds.length} selected)
                </label>
                {classes.length > 0 && (
                  <button
                    type="button"
                    onClick={() => {
                      if (selectedClassIds.length === classes.length) {
                        setSelectedClassIds([]);
                      } else {
                        setSelectedClassIds(classes.map((c) => c.id));
                      }
                    }}
                    className="text-xs text-indigo-400 hover:underline"
                  >
                    {selectedClassIds.length === classes.length ? "Deselect All" : "Select All"}
                  </button>
                )}
              </div>

              <div className="max-h-56 overflow-y-auto space-y-1.5 p-2 rounded-2xl bg-zinc-950/60 border border-zinc-800">
                {classes.map((c) => {
                  const isSelected = selectedClassIds.includes(c.id);
                  return (
                    <div
                      key={c.id}
                      onClick={() => toggleClassSelection(c.id)}
                      className={`flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition-colors text-xs ${
                        isSelected
                          ? "bg-indigo-600/20 border border-indigo-500/40 text-white font-medium"
                          : "hover:bg-zinc-800/60 text-zinc-300 border border-transparent"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <BookOpen size={14} className={isSelected ? "text-indigo-400" : "text-zinc-500"} />
                        <span>{c.name} {c.section}</span>
                      </div>
                      <div
                        className={`w-4 h-4 rounded border flex items-center justify-center ${
                          isSelected
                            ? "bg-indigo-600 border-indigo-500 text-white"
                            : "border-zinc-600 bg-zinc-800"
                        }`}
                      >
                        {isSelected && <Check size={12} />}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-zinc-800">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsAssignModalOpen(false)}
                disabled={assignLoading}
                className="text-zinc-400 hover:text-white"
              >
                Cancel
              </Button>
              <Button
                size="sm"
                className="bg-indigo-600 hover:bg-indigo-700 text-white"
                onClick={handleAssignClasses}
                disabled={assignLoading || teachers.length === 0}
              >
                {assignLoading ? "Assigning..." : "Assign Classes"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

