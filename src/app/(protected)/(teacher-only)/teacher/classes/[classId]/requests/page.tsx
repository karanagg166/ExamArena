"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Check, Clock3, Hash, X } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/loading";
import { useJoinRequestStore, useSchoolClassStore } from "@/stores";
import type { ClassJoinRequest } from "@/types";

export default function ClassRequestsPage() {
  const { classId } = useParams<{ classId: string }>();
  const router = useRouter();
  const { classRequests, loading, error, fetchClassRequests, decideRequest } = useJoinRequestStore();
  const { classes, fetchClass } = useSchoolClassStore();

  const [approvingReq, setApprovingReq] = useState<ClassJoinRequest | null>(null);
  const [rollNoMode, setRollNoMode] = useState<"AUTO" | "CUSTOM">("AUTO");
  const [customRollNo, setCustomRollNo] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const currentClass = classes.find((c) => c.id === classId);

  useEffect(() => {
    if (classId) {
      void fetchClassRequests(classId);
      if (!currentClass) void fetchClass(classId);
    }
  }, [classId, fetchClassRequests, currentClass, fetchClass]);

  const handleReject = async (requestId: string) => {
    setIsSubmitting(true);
    const result = await decideRequest(requestId, "REJECTED");
    if (result.success) {
      toast.success("Join request rejected.");
    } else {
      toast.error(result.error ?? "Unable to reject request.");
    }
    setIsSubmitting(false);
  };

  const handleOpenApprove = (req: ClassJoinRequest) => {
    setApprovingReq(req);
    setRollNoMode("AUTO");
    setCustomRollNo("");
  };

  const handleConfirmApprove = async () => {
    if (!approvingReq) return;
    const cleanedRollNo = customRollNo.trim().replace(/\D/g, "");
    if (rollNoMode === "CUSTOM" && !cleanedRollNo) {
      toast.error("Please enter a numeric roll number (numbers only) or select Auto.");
      return;
    }

    setIsSubmitting(true);
    const result = await decideRequest(approvingReq.id, "APPROVED", {
      rollNo: rollNoMode === "CUSTOM" ? cleanedRollNo : undefined,
      autoRollNo: rollNoMode === "AUTO",
    });

    if (result.success) {
      toast.success("Student approved and permanently assigned roll number.");
      setApprovingReq(null);
    } else {
      toast.error(result.error ?? "Unable to approve request.");
    }
    setIsSubmitting(false);
  };

  return (
    <div className="page-shell text-white">
      <div className="mx-auto max-w-4xl space-y-6">
        <Button variant="ghost" className="text-zinc-400 hover:text-white" onClick={() => router.back()}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to {currentClass?.name || "Class"}
        </Button>
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-amber-400/10 p-2 text-amber-300"><Clock3 className="h-5 w-5" /></div>
              <div>
                <CardTitle>
                  Pending enrollment requests{currentClass?.name ? ` — ${currentClass.name}` : ""}
                </CardTitle>
                <p className="mt-1 text-sm text-zinc-400">
                  Approve and assign a permanent, immutable roll number to each student.
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex min-h-40 items-center justify-center"><Spinner className="h-7 w-7 border-4" /></div>
            ) : error ? (
              <p className="text-sm text-red-300">{error}</p>
            ) : classRequests.length === 0 ? (
              <div className="rounded-xl border border-dashed border-zinc-700 p-8 text-center text-sm text-zinc-500">No pending join requests.</div>
            ) : (
              <div className="divide-y divide-zinc-800 rounded-xl border border-zinc-800">
                {classRequests.map((request) => (
                  <div key={request.id} className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="font-medium text-zinc-100">{request.studentName}</p>
                      <p className="text-sm text-zinc-400">{request.studentEmail}</p>
                      <p className="mt-1 text-xs text-zinc-500">Requested {new Date(request.requestedAt).toLocaleString()}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={isSubmitting}
                        onClick={() => void handleReject(request.id)}
                      >
                        <X className="mr-1.5 h-4 w-4" /> Reject
                      </Button>
                      <Button
                        size="sm"
                        disabled={isSubmitting}
                        onClick={() => handleOpenApprove(request)}
                      >
                        <Check className="mr-1.5 h-4 w-4" /> Approve & Assign Roll No
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Approve & Assign Roll Number Modal */}
        {approvingReq && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-3xl p-6 shadow-2xl space-y-5 animate-in zoom-in-95 duration-200">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-xl font-bold text-white">
                    Approve Student Enrollment
                  </h3>
                  <p className="text-xs text-zinc-400 mt-1">
                    Student: <strong>{approvingReq.studentName}</strong>
                  </p>
                </div>
                <button
                  onClick={() => setApprovingReq(null)}
                  className="text-zinc-500 hover:text-white"
                >
                  ✕
                </button>
              </div>

              <div className="rounded-xl bg-zinc-950/60 p-3.5 border border-zinc-800 text-xs space-y-1 text-zinc-300">
                <p><strong>Email:</strong> {approvingReq.studentEmail}</p>
                <p><strong>Class:</strong> {approvingReq.className}</p>
                <p className="text-amber-400 font-semibold pt-1">
                  Note: Roll numbers are permanently locked once approved.
                </p>
              </div>

              <div className="space-y-3">
                <label className="text-xs font-bold uppercase tracking-wider text-zinc-400">
                  Roll Number Mode
                </label>

                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setRollNoMode("AUTO")}
                    className={`p-3 rounded-xl border text-left text-xs font-semibold transition-all ${
                      rollNoMode === "AUTO"
                        ? "border-indigo-500 bg-indigo-950/30 text-indigo-400 ring-2 ring-indigo-500/20"
                        : "border-zinc-800 text-zinc-400 hover:border-zinc-700"
                    }`}
                  >
                    Automatic Next
                    <p className="text-[10px] font-normal text-zinc-500 mt-0.5">
                      Sequential roll number
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setRollNoMode("CUSTOM")}
                    className={`p-3 rounded-xl border text-left text-xs font-semibold transition-all ${
                      rollNoMode === "CUSTOM"
                        ? "border-indigo-500 bg-indigo-950/30 text-indigo-400 ring-2 ring-indigo-500/20"
                        : "border-zinc-800 text-zinc-400 hover:border-zinc-700"
                    }`}
                  >
                    Custom Roll No
                    <p className="text-[10px] font-normal text-zinc-500 mt-0.5">
                      Enter manual number
                    </p>
                  </button>
                </div>

                {rollNoMode === "CUSTOM" && (
                  <div className="space-y-1.5 pt-1">
                    <label className="text-xs text-zinc-400">Enter Roll Number</label>
                    <div className="relative">
                      <Hash size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
                      <input
                        type="text"
                        inputMode="numeric"
                        pattern="[0-9]*"
                        value={customRollNo}
                        onChange={(e) => setCustomRollNo(e.target.value.replace(/\D/g, ""))}
                        placeholder="e.g. 101, 102 (numbers only)"
                        className="w-full pl-8 pr-4 py-2 text-sm rounded-xl border border-zinc-700 bg-zinc-800 text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-zinc-800">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setApprovingReq(null)}
                  disabled={isSubmitting}
                  className="text-zinc-400 hover:text-white"
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                  onClick={handleConfirmApprove}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Enrolling..." : "Confirm & Enroll"}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

