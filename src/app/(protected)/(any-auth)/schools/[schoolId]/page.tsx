"use client";
import { useEffect } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/loading";
import { useSchoolStore } from "@/stores/index";

export default function SchoolPage() {
  const { schoolId } = useParams<{ schoolId: string }>();
  const { fetchSchoolById, school, loading, error } = useSchoolStore();
  console.log("Fetching school details for ID:", schoolId);
  useEffect(() => {
    if (schoolId) fetchSchoolById(schoolId);
  }, [schoolId, fetchSchoolById]);

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
            <CardTitle className="text-red-300">
              Unable to load school
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-red-200">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!school) return null;

  return (
    <div className="page-shell text-white">
      <Card className="max-w-3xl">
        <CardHeader>
          <CardTitle className="text-2xl">{school.name}</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 text-sm text-zinc-300 sm:grid-cols-2">
          <p>
            <span className="text-zinc-500">City:</span> {school.city || "-"}
          </p>
          <p>
            <span className="text-zinc-500">State:</span> {school.state || "-"}
          </p>
          <p>
            <span className="text-zinc-500">Country:</span>{" "}
            {school.country || "-"}
          </p>
          <p>
            <span className="text-zinc-500">Pincode:</span>{" "}
            {school.pincode || "-"}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
