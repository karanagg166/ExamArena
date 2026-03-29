"use client";
import { useEffect } from "react";
import { useSchoolStore, useSchoolClassStore } from "@/stores";
import SchoolClassCard from "@/components/school-class/SchoolClassCard";
import { Spinner } from "@/components/ui/loading";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";

export default function PrincipalSchoolClassPage() {
  const router = useRouter();
  const { school, loading: schoolLoading, fetchSchool } = useSchoolStore();
  const {
    classes,
    loading: classesLoading,
    fetchClassesBySchool,
  } = useSchoolClassStore();

  useEffect(() => {
    if (!school) fetchSchool();
  }, [school, fetchSchool]);

  useEffect(() => {
    if (school?.id) fetchClassesBySchool(school.id);
  }, [school?.id, fetchClassesBySchool]);

  if (schoolLoading || classesLoading) {
    return (
      <div className="flex min-h-[80vh] items-center justify-center">
        <Spinner className="h-10 w-10 text-indigo-500 border-4" />
      </div>
    );
  }

  if (!school) {
    return (
      <div className="flex min-h-[80vh] items-center justify-center">
        <p className="text-zinc-500">
          No school found. Please set up your school first.
        </p>
      </div>
    );
  }

  return (
    <div className="page-shell text-white p-6 max-w-6xl mx-auto space-y-8">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          className="text-zinc-400 hover:text-white"
          onClick={() => router.back()}
        >
          <ArrowLeft className="w-4 h-4 mr-2" /> Back
        </Button>
      </div>

      <Card className="border-zinc-800 bg-zinc-950/50">
        <CardHeader>
          <CardTitle className="text-3xl font-bold tracking-tight">
            Classes Directory
          </CardTitle>
          <CardDescription className="text-zinc-400">
            Overview of all classes in {school.name}. Click into a class to view
            its specific details and student roster.
          </CardDescription>
        </CardHeader>
      </Card>

      {classes.length === 0 ? (
        <div className="flex min-h-[40vh] items-center justify-center rounded-2xl border border-zinc-800 border-dashed bg-zinc-900/20">
          <p className="text-zinc-500">No classes found in this school.</p>
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {classes.map((cls) => (
            <SchoolClassCard key={cls.id} schoolClass={cls} />
          ))}
        </div>
      )}
    </div>
  );
}
