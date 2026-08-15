"use client";
import { useEffect, useState } from "react";
import { useSchoolStore, useSchoolClassStore } from "@/stores";
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
import { ArrowLeft, Plus, UserPlus, Check, X } from "lucide-react";
import { api } from "@/lib/axios";

export default function PrincipalSchoolClassPage() {
  const router = useRouter();
  const { school, loading: schoolLoading, fetchSchool } = useSchoolStore();
  const {
    classes,
    loading: classesLoading,
    fetchClassesBySchool,
  } = useSchoolClassStore();

  const [requestModalOpen, setRequestModalOpen] = useState(false);
  const [selectedClassId, setSelectedClassId] = useState("");
  const [selectedSubject, setSelectedSubject] = useState("MATHEMATICS");
  const [requesting, setRequesting] = useState(false);
  const [requestSuccess, setRequestSuccess] = useState<string | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);

  useEffect(() => {
    if (!school) fetchSchool();
  }, [school, fetchSchool]);

  useEffect(() => {
    if (school?.id) fetchClassesBySchool(school.id);
  }, [school?.id, fetchClassesBySchool]);

  const handleSendRequest = async () => {
    if (!selectedClassId) {
      setRequestError("Please select a class.");
      return;
    }
    setRequesting(true);
    setRequestError(null);
    setRequestSuccess(null);
    try {
      await api.post("/api/v1/teacher-requests", {
        classId: selectedClassId,
        subject: selectedSubject || null,
      });
      setRequestSuccess("Your request to teach this class has been sent to the Principal for approval!");
      setTimeout(() => {
        setRequestModalOpen(false);
        setRequestSuccess(null);
      }, 2500);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail;
      setRequestError(detail ?? "Failed to submit request.");
    } finally {
      setRequesting(false);
    }
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
      <div className="flex min-h-[70vh] flex-col items-center justify-center p-6 text-center">
        <div className="max-w-lg rounded-2xl border border-zinc-800 bg-zinc-950/60 p-8 shadow-xl space-y-4">
          <h2 className="text-2xl font-bold text-white">No School Associated</h2>
          <p className="text-sm text-zinc-400">
            You must be connected to a school to view or manage classes. You can join an existing school or become a Principal to start your own school.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
            <Button onClick={() => router.push("/teacher/school/join")}>
              Join a School →
            </Button>
            <Button variant="secondary" onClick={() => router.push("/signup/principal/create-school")}>
              Start Your Own School
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
        <CardHeader className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <CardTitle className="text-3xl font-bold tracking-tight">
              Classes Directory
            </CardTitle>
            <CardDescription className="text-zinc-400">
              Overview of all classes in {school.name}. Click into a class to view
              its specific details and student roster.
            </CardDescription>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              onClick={() => {
                setRequestModalOpen(true);
                if (classes.length > 0 && !selectedClassId) {
                  setSelectedClassId(classes[0].id);
                }
              }}
              className="border-indigo-500/40 text-indigo-400 hover:bg-indigo-950/30"
            >
              <UserPlus className="mr-2 h-4 w-4" />
              Request to Teach Class
            </Button>
            <Button onClick={() => router.push("/teacher/classes/new")}>
              <Plus className="mr-2 h-4 w-4" />
              Create Class
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Modal for Requesting to Teach a Class */}
      {requestModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-zinc-800 bg-zinc-900 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <UserPlus size={18} className="text-indigo-400" />
                Request to Teach a Class
              </h3>
              <button
                onClick={() => setRequestModalOpen(false)}
                className="text-zinc-400 hover:text-white"
              >
                <X size={18} />
              </button>
            </div>

            <p className="text-xs text-zinc-400">
              Select a class and your primary subject. Your request will be sent to the Principal for review and approval.
            </p>

            {requestSuccess ? (
              <div className="rounded-xl bg-emerald-950/50 border border-emerald-500/40 p-4 text-emerald-300 text-sm flex items-center gap-3">
                <Check className="h-5 w-5 text-emerald-400 shrink-0" />
                {requestSuccess}
              </div>
            ) : (
              <div className="space-y-4 pt-2">
                {requestError && (
                  <div className="rounded-xl bg-red-950/50 border border-red-500/40 p-3 text-red-300 text-xs">
                    {requestError}
                  </div>
                )}

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-zinc-300">Target Class</label>
                  <select
                    value={selectedClassId}
                    onChange={(e) => setSelectedClassId(e.target.value)}
                    className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">Select a class</option>
                    {classes.map((cls) => (
                      <option key={cls.id} value={cls.id}>
                        {cls.name} (Section {cls.section}) — Year {cls.year}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-zinc-300">Subject</label>
                  <select
                    value={selectedSubject}
                    onChange={(e) => setSelectedSubject(e.target.value)}
                    className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="MATHEMATICS">Mathematics</option>
                    <option value="PHYSICS">Physics</option>
                    <option value="CHEMISTRY">Chemistry</option>
                    <option value="BIOLOGY">Biology</option>
                    <option value="ENGLISH">English</option>
                    <option value="HISTORY">History</option>
                    <option value="GEOGRAPHY">Geography</option>
                    <option value="COMPUTER_SCIENCE">Computer Science</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>

                <div className="flex items-center justify-end gap-3 pt-3">
                  <Button
                    variant="ghost"
                    onClick={() => setRequestModalOpen(false)}
                    disabled={requesting}
                    className="text-zinc-400"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSendRequest}
                    disabled={requesting || !selectedClassId}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white"
                  >
                    {requesting ? "Sending..." : "Submit Request"}
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

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
    </div>
  );
}
