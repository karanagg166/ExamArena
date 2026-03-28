"use client";
import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/axios";
import { SchoolClass } from "@/types/school-class";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { FormMessage } from "@/components/ui/form-message";
import { Spinner } from "@/components/ui/loading";

export const Page = () => {
  const router = useRouter();
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchClasses = async () => {
      try {
        const schoolResponse = await api.get("/api/v1/schools/me");
        const response = await api.get(
          `/api/v1/classes/school/${schoolResponse.data.id}`,
        );
        setClasses(response.data);
      } catch (error) {
        console.error("Failed to fetch classes:", error);
        setError("Failed to load classes");
      } finally {
        setLoading(false);
      }
    };

    fetchClasses();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="h-8 w-8 border-4" />
      </div>
    );
  }

  return (
    <div className="page-shell text-white">
      <Card className="mb-4">
        <CardHeader className="flex flex-row items-center justify-between gap-3">
          <div>
            <CardTitle>Classes</CardTitle>
            <CardDescription>View and manage school classes.</CardDescription>
          </div>
          <Button onClick={() => router.push("/principal/school/school-class")}>
            New Class
          </Button>
        </CardHeader>
      </Card>

      <FormMessage message={error} type="error" className="mb-4" />

      {classes.length === 0 ? (
        <p className="text-sm text-zinc-400">
          No classes found. Create one to get started.
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {classes.map((schoolClass) => (
            <Card key={schoolClass.id}>
              <CardContent className="pt-5">
                <p className="text-sm font-medium text-zinc-200">
                  {schoolClass.name}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
