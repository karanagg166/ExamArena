"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Check, Clock3, X } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/loading";
import { useJoinRequestStore, useSchoolClassStore } from "@/stores";

export default function ClassRequestsPage() {
  const { classId } = useParams<{ classId: string }>();
  const router = useRouter();
  const { classRequests, loading, error, fetchClassRequests, decideRequest } = useJoinRequestStore();
  const { classes, fetchClass } = useSchoolClassStore();

  const currentClass = classes.find((c) => c.id === classId);

  useEffect(() => {
    if (classId) {
      void fetchClassRequests(classId);
      if (!currentClass) void fetchClass(classId);
    }
  }, [classId, fetchClassRequests, currentClass, fetchClass]);

  const decide = async (requestId: string, status: "APPROVED" | "REJECTED") => {
    const result = await decideRequest(requestId, status);
    if (result.success) {
      toast.success(status === "APPROVED" ? "Student approved and enrolled." : "Join request rejected.");
    } else {
      toast.error(result.error ?? "Unable to update the request.");
    }
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
                <p className="mt-1 text-sm text-zinc-400">Approving assigns the next permanent roll number in this class.</p>
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
                      <Button size="sm" variant="outline" onClick={() => void decide(request.id, "REJECTED")}>
                        <X className="mr-1.5 h-4 w-4" /> Reject
                      </Button>
                      <Button size="sm" onClick={() => void decide(request.id, "APPROVED")}>
                        <Check className="mr-1.5 h-4 w-4" /> Approve
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
