"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/axios";
import { School } from "@/types/school";
import SchoolProfileCard from "@/components/school/SchoolProfileCard";
import { Spinner } from "@/components/ui/loading";
import { Building2 } from "lucide-react";

export default function PrincipalSchoolPage() {
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
        console.error("Failed to fetch school:", error);
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
      <div className="page-shell">
        <div className="max-w-lg mx-auto text-center mt-20 p-8 rounded-2xl border border-zinc-800 bg-zinc-950/60 shadow-xl">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Building2 className="h-7 w-7" />
          </div>
          <h2 className="text-2xl font-bold text-white">
            No School Associated
          </h2>
          <p className="text-zinc-400 mt-2 text-sm">
            You are not connected to any school yet. Join an existing school to access classes, students, and exams.
          </p>
          <div className="mt-6">
            <button
              onClick={() => router.push("/teacher/school/join")}
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-xl transition-all shadow-lg shadow-indigo-600/20"
            >
              Join a School →
            </button>
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
