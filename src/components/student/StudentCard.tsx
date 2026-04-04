"use client";

import { useRouter } from "next/navigation";

export type StudentListItem = {
  id: string;
  userId: string;
  rollNo: string;
  classId: string;
  schoolId: string;
  name: string;
  email: string;
  phoneNo?: string | null;
};

interface StudentCardProps {
  student: StudentListItem;
}

export default function StudentCard({ student }: StudentCardProps) {
  const router = useRouter();

  return (
    <div
      onClick={() => router.push(`/students/${student.id}`)}
      className="group relative overflow-hidden rounded-2xl border border-gray-100 bg-white p-5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md cursor-pointer"
    >
      {/* top accent bar */}
      <div className="absolute left-0 top-0 h-1 w-full bg-gradient-to-r from-indigo-500 to-violet-500 opacity-0 transition-opacity duration-200 group-hover:opacity-100" />

      <div className="mb-4 flex items-start justify-between gap-3">
        {/* Avatar initial */}
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-100 to-violet-100 text-sm font-bold text-indigo-700">
            {student.name.charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0">
            <h3 className="truncate text-base font-semibold text-gray-900">
              {student.name}
            </h3>
            <p className="mt-0.5 text-xs text-indigo-600 truncate">
              {student.email}
            </p>
          </div>
        </div>
        <span className="shrink-0 rounded-full border border-violet-100 bg-violet-50 px-2.5 py-1 text-xs font-medium text-violet-700">
          Roll #{student.rollNo}
        </span>
      </div>

      {student.phoneNo && (
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span>📞</span>
          <span className="truncate text-xs">{student.phoneNo}</span>
        </div>
      )}
    </div>
  );
}
