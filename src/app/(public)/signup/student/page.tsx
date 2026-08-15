"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { KeyRound, ShieldCheck } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useJoinRequestStore } from "@/stores";

export default function SignupStudentPage() {
  const router = useRouter();
  const { joinByCode, loading, error } = useJoinRequestStore();
  const [joinCode, setJoinCode] = useState("");

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const result = await joinByCode(joinCode.trim().toUpperCase());
    if (!result.success) {
      toast.error(result.error ?? "Unable to submit the join request.");
      return;
    }
    toast.success("Join request sent to your class teacher.");
    router.push("/student/profile");
  };

  return (
    <div className="page-shell flex min-h-screen items-center justify-center py-12 text-white">
      <Card className="w-full max-w-xl shadow-2xl shadow-indigo-950/20">
        <CardHeader className="space-y-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-indigo-400/30 bg-indigo-500/10 text-indigo-300">
            <KeyRound className="h-5 w-5" />
          </div>
          <div>
            <CardTitle className="text-2xl">Request to join your class</CardTitle>
            <CardDescription className="mt-1">
              Enter the code shared by your teacher. They will review your request before your roll number is assigned.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="join-code">Class join code</Label>
              <Input
                id="join-code"
                value={joinCode}
                onChange={(event) => setJoinCode(event.target.value.toUpperCase())}
                placeholder="e.g. 8F2KQ9XA"
                autoCapitalize="characters"
                autoComplete="off"
                className="font-mono uppercase tracking-[0.18em]"
                required
              />
              {error && <p className="text-sm text-red-300">{error}</p>}
            </div>
            <div className="flex gap-3 rounded-xl border border-zinc-800 bg-zinc-900/50 p-3 text-sm text-zinc-400">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
              Your class, school, and roll number are assigned securely by the school after approval.
            </div>
            <Button type="submit" className="w-full" disabled={loading || !joinCode.trim()}>
              {loading ? "Sending request…" : "Send join request"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
