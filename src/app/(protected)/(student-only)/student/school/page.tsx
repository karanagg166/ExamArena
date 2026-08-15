"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/axios";
import { School } from "@/types/school";
import SchoolProfileCard from "@/components/school/SchoolProfileCard";
import { Spinner } from "@/components/ui/loading";

import { GraduationCap, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";

export default function StudentSchoolPage() {
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
        <div className="max-w-xl mx-auto text-center space-y-6 animate-fade-in-up">
          <GlassCard className="p-8 sm:p-10 border-[var(--border-subtle)] space-y-6">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <GraduationCap className="h-8 w-8" />
            </div>

            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-slate-800 dark:text-white">
                No School Joined Yet
              </h2>
              <p className="text-sm text-slate-600 dark:text-zinc-400 max-w-md mx-auto">
                You haven&apos;t joined a school yet. Contact your school principal or teacher to be assigned to your class and start taking exams.
              </p>
            </div>

            <div className="flex justify-center pt-2">
              <Button
                variant="primary"
                onClick={() => router.push("/schools")}
                className="shadow-glow"
              >
                Browse Schools Directory
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </GlassCard>
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
