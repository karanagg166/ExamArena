"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/axios";
import { Spinner } from "@/components/ui/loading";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ArrowLeft,
  Mail,
  Phone,
  MapPin,
  Calendar,
  Hash,
  Users,
  User,
  School,
  BookOpen,
} from "lucide-react";

/** Shape returned by GET /api/v1/students/:id */
type StudentDetailResponse = {
  id: string;
  userId: string;
  rollNo: string;
  parentName: string;
  parentEmail: string;
  dateOfAdmission: string;
  schoolId: string;
  classId: string;
  user: {
    id: string;
    name: string;
    email: string;
    phoneNo: string;
    city: string;
    state: string;
    country: string;
    pincode: string;
  };
};

const fmt = (ds: string) => {
  try {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "2-digit",
      year: "numeric",
    }).format(new Date(ds));
  } catch {
    return "—";
  }
};

export default function StudentDetailPage() {
  const { studentId } = useParams<{ studentId: string }>();
  const router = useRouter();
  const [student, setStudent] = useState<StudentDetailResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStudent = async () => {
      setLoading(true);
      setError(null);
      try {
        const { data } = await api.get<StudentDetailResponse>(
          `/api/v1/students/${studentId}`,
        );
        setStudent(data);
      } catch (err: unknown) {
        const detail =
          (err as { response?: { data?: { detail?: string } } })?.response
            ?.data?.detail;
        setError(detail ?? (err as Error)?.message ?? "Something went wrong");
      } finally {
        setLoading(false);
      }
    };

    if (studentId) fetchStudent();
  }, [studentId]);

  if (loading) {
    return (
      <div className="flex min-h-[80vh] items-center justify-center rounded-xl m-4 bg-gray-50/50 dark:bg-slate-900/50">
        <Spinner className="h-10 w-10 text-indigo-600 border-4" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 min-h-[80vh] flex items-center justify-center">
        <Card className="max-w-md w-full border-red-500/30 shadow-red-500/10 shadow-xl">
          <CardHeader>
            <CardTitle className="text-red-500 flex items-center gap-2">
              <span>⚠️</span> Unable to load profile
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-600 dark:text-slate-300">{error}</p>
            <Button
              variant="outline"
              onClick={() => router.back()}
              className="w-full"
            >
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!student) return null;

  const { user } = student;

  return (
    <div className="p-4 md:p-8 min-h-screen bg-transparent">
      {/* Back button */}
      <div className="max-w-4xl mx-auto mb-6">
        <Button
          variant="ghost"
          onClick={() => router.back()}
          className="text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 flex items-center gap-2 -ml-4"
        >
          <ArrowLeft size={16} />
          Back to Students
        </Button>
      </div>

      <div className="w-full max-w-4xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
        {/* Hero card */}
        <Card className="overflow-hidden border-none shadow-xl bg-gradient-to-br from-indigo-50 to-white dark:from-slate-900 dark:to-slate-950">
          {/* Banner */}
          <div className="h-32 bg-gradient-to-r from-indigo-500/20 via-violet-500/10 to-transparent w-full" />

          <CardContent className="relative px-8 pb-8 pt-0">
            <div className="-mt-16 mb-4 relative z-10 flex flex-col md:flex-row items-center md:items-end gap-6">
              {/* Avatar */}
              <div className="w-32 h-32 rounded-2xl bg-white dark:bg-slate-800 p-2 shadow-lg flex-shrink-0 border border-indigo-100 dark:border-indigo-900/50">
                <div className="w-full h-full bg-indigo-50 dark:bg-indigo-900/20 rounded-xl flex items-center justify-center text-indigo-400">
                  <User size={48} className="opacity-50" />
                </div>
              </div>

              {/* Name / Roll */}
              <div className="flex-1 text-center md:text-left mb-2">
                <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                  {user.name}
                </h1>
                <p className="text-indigo-600 dark:text-indigo-400 font-medium flex items-center justify-center md:justify-start gap-2 mt-1">
                  <Hash size={16} />
                  Roll No: {student.rollNo} &nbsp;•&nbsp; Admitted{" "}
                  {fmt(student.dateOfAdmission)}
                </p>
              </div>

              <div className="mb-2 hidden md:block">
                <Badge className="px-4 py-2 text-sm bg-indigo-100 text-indigo-800 hover:bg-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-300 border-none shadow-sm">
                  Student
                </Badge>
              </div>
            </div>

            {/* Details grid */}
            <div className="grid md:grid-cols-2 gap-8 mt-8 border-t border-slate-100 dark:border-slate-800/50 pt-8">
              {/* Personal info */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                  Personal Information
                </h3>
                <div className="space-y-3">
                  <InfoRow icon={<Mail size={16} />} value={user.email} />
                  <InfoRow icon={<Phone size={16} />} value={user.phoneNo} />
                  <InfoRow
                    icon={<MapPin size={16} />}
                    value={
                      [user.city, user.state, user.country, user.pincode]
                        .filter(Boolean)
                        .join(", ") || "No address provided"
                    }
                  />
                  <InfoRow
                    icon={<Calendar size={16} />}
                    value={`Admitted: ${fmt(student.dateOfAdmission)}`}
                  />
                </div>
              </div>

              {/* Guardian info */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider flex items-center gap-2">
                  <Users size={16} />
                  Guardian Details
                </h3>
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 space-y-3">
                  <DetailRow label="Parent Name" value={student.parentName} />
                  <DetailRow
                    label="Parent Email"
                    value={
                      <a
                        href={`mailto:${student.parentEmail}`}
                        className="font-medium text-indigo-600 hover:underline"
                      >
                        {student.parentEmail}
                      </a>
                    }
                  />
                </div>

                {/* School / Class IDs */}
                <h3 className="text-sm font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider flex items-center gap-2 pt-2">
                  <School size={16} />
                  Enrolment
                </h3>
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 space-y-3">
                  <DetailRow
                    label="School ID"
                    value={
                      <span className="font-mono text-xs text-slate-600 dark:text-slate-300">
                        {student.schoolId}
                      </span>
                    }
                  />
                  <DetailRow
                    label="Class ID"
                    value={
                      <span className="font-mono text-xs text-slate-600 dark:text-slate-300">
                        {student.classId}
                      </span>
                    }
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

/* ─── Small helpers ───────────────────────────────────────────── */

function InfoRow({
  icon,
  value,
}: {
  icon: React.ReactNode;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-3 text-slate-700 dark:text-slate-300">
      <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500 flex-shrink-0 mt-0.5">
        {icon}
      </div>
      <span className="mt-1 leading-relaxed">{value}</span>
    </div>
  );
}

function DetailRow({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-sm text-slate-500 shrink-0">{label}</span>
      <span className="font-medium text-slate-800 dark:text-slate-200 text-right">
        {value}
      </span>
    </div>
  );
}
