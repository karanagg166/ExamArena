"use client";

import type { Teacher } from "@/types/teacher";
import { useRouter } from "next/navigation";

interface TeacherCardProps {
  teacher: Teacher;
}

export default function TeacherCard({ teacher }: TeacherCardProps) {
  const router = useRouter();

  return (
    <div
      onClick={() => router.push(`/teachers/${teacher.id}`)}
      className="group relative overflow-hidden rounded-2xl border border-gray-100 bg-white p-5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md cursor-pointer"
    >
      <div className="absolute left-0 top-0 h-1 w-full bg-gradient-to-r from-violet-500 to-indigo-500 opacity-0 transition-opacity duration-200 group-hover:opacity-100" />

      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-base font-semibold text-gray-900">
            {teacher.name}
          </h3>
          <p className="mt-0.5 text-xs text-indigo-600">{teacher.department}</p>
        </div>
        <span className="shrink-0 rounded-full border border-violet-100 bg-violet-50 px-2.5 py-1 text-xs font-medium text-violet-700">
          {teacher.experience} yr{teacher.experience !== 1 ? "s" : ""} exp
        </span>
      </div>

      <div className="space-y-2 text-sm">
        <Detail icon="📧" value={teacher.email} />
        <Detail icon="📞" value={teacher.phoneNo} />
      </div>

      {teacher.subjects.length > 0 && (
        <div className="mt-4">
          <p className="mb-1.5 text-[10px] uppercase tracking-wide text-gray-400">
            Subjects
          </p>
          <div className="flex flex-wrap gap-1.5">
            {teacher.subjects.map((subject) => (
              <span
                key={subject}
                className="rounded-full border border-indigo-100 bg-indigo-50 px-2 py-0.5 text-xs text-indigo-700"
              >
                {subject}
              </span>
            ))}
          </div>
        </div>
      )}

      {teacher.qualifications.length > 0 && (
        <div className="mt-3">
          <p className="mb-1.5 text-[10px] uppercase tracking-wide text-gray-400">
            Qualifications
          </p>
          <div className="flex flex-wrap gap-1.5">
            {teacher.qualifications.map((q) => (
              <span
                key={q}
                className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
              >
                {q}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Detail({ icon, value }: { icon: string; value: string }) {
  return (
    <div className="flex items-center gap-2 truncate text-gray-600">
      <span className="shrink-0">{icon}</span>
      <span className="truncate text-xs">{value || "-"}</span>
    </div>
  );
}
