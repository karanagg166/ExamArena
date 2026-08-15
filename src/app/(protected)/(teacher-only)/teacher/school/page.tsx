"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/axios";
import { School } from "@/types/school";
import SchoolProfileCard from "@/components/school/SchoolProfileCard";
import { Spinner } from "@/components/ui/loading";
import { Building2, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";

export default function TeacherSchoolPage() {
  const [school, setSchool] = useState<School | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const fetchSchool = async () => {
      try {
        const response = await api.get("/api/v1/schools/me", {
          withCredentials: true,
        });
        setSchool(response.data);
      } catch (error) {
        const status = (error as { response?: { status?: number } })?.response?.status;
        if (status !== 404) {
          console.error("Failed to fetch school:", error);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchSchool();
  }, [router]);

  if (loading) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center">
        <Spinner className="h-8 w-8 border-4" />
      </div>
    );
  }

  if (!school) {
    return (
      <div className="page-shell py-12">
        <div className="max-w-3xl mx-auto space-y-8 animate-fade-in-up">
          <div className="text-center space-y-3">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Building2 className="h-8 w-8" />
            </div>
            <h2 className="text-3xl font-bold text-slate-800 dark:text-white">
              No School Associated Yet
            </h2>
            <p className="text-sm text-slate-600 dark:text-zinc-400 max-w-lg mx-auto">
              You are currently not connected to any school. You can join an existing school as a teacher or become a Principal to start your own school.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Card 1: Join School */}
            <GlassCard className="p-6 flex flex-col justify-between space-y-6 border-[var(--border-subtle)] hover:border-indigo-500/40 transition-all">
              <div className="space-y-3">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-zinc-800 text-zinc-300 border border-zinc-700">
                  Teacher Option
                </span>
                <h3 className="text-xl font-bold text-slate-800 dark:text-white">
                  Join Existing School
                </h3>
                <p className="text-sm text-slate-600 dark:text-zinc-400">
                  Submit a teacher join request to an existing school principal to be assigned to classes and subjects.
                </p>
              </div>

              <div className="space-y-2 pt-4">
                <Button
                  variant="primary"
                  onClick={() => router.push("/teacher/school/join")}
                  className="w-full shadow-glow"
                >
                  Join a School
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => router.push("/schools")}
                  className="w-full"
                >
                  Browse Schools Directory
                </Button>
              </div>
            </GlassCard>

            {/* Card 2: Become Principal & Start School */}
            <GlassCard className="p-6 flex flex-col justify-between space-y-6 border-indigo-500/30 bg-gradient-to-b from-indigo-950/20 to-zinc-950/40 hover:border-indigo-500/60 transition-all">
              <div className="space-y-3">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Principal Role
                </span>
                <h3 className="text-xl font-bold text-slate-800 dark:text-white">
                  Become a Principal & Start School
                </h3>
                <p className="text-sm text-slate-600 dark:text-zinc-400">
                  Establish your own institution, create classes, invite teachers, and manage school-wide assessments as a Principal.
                </p>
              </div>

              <div className="pt-4">
                <Button
                  variant="primary"
                  onClick={() => router.push("/signup/principal/create-school")}
                  className="w-full bg-indigo-600 hover:bg-indigo-500 text-white shadow-glow"
                >
                  Start Your Own School
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </GlassCard>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-shell py-8">
      <SchoolProfileCard school={school} />
    </div>
  );
}
