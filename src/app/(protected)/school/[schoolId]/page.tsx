"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/axios";
import type { School } from "@/types/school";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/loading";

export default function SchoolPage() {
  const { schoolId } = useParams<{ schoolId: string }>();
  const [school, setSchool] = useState<School | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSchool = async () => {
      setLoading(true);
      setError(null);
      try {
        const { data } = await api.get<School>(`/api/v1/schools/${schoolId}`);
        setSchool(data);
      } catch (err: unknown) {
        setError((err as Error)?.message ?? "Something went wrong");
      } finally {
        setLoading(false);
      }
    };

    if (schoolId) fetchSchool();
  }, [schoolId]);

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
