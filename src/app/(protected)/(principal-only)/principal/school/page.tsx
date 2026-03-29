"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/axios";
import { School } from "@/types/school";
import SchoolProfileCard from "@/components/school/SchoolProfileCard";
import { Spinner } from "@/components/ui/loading";

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
        <div className="max-w-4xl mx-auto text-center mt-20">
          <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-200">
            No School Found
          </h2>
          <p className="text-slate-500 mt-2">
            You are not associated with any school yet.
          </p>
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
