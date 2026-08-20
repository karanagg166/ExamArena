import type { SchoolClass } from "@/types/index";
import { useRouter } from "next/navigation";
import { Copy, Trash2, Check } from "lucide-react";
import { useSchoolClassStore, useAuthStore } from "@/stores";
import { toast } from "sonner";
import { formatDateIST } from "@/lib/date";

interface SchoolClassCardProps {
  schoolClass: SchoolClass;
  basePath?: string;
  showDelete?: boolean;
  isTeacherAssigned?: boolean;
  onRequestJoin?: (classId: string) => void;
}

export default function SchoolClassCard({
  schoolClass,
  basePath = "/principal/school/classes",
  showDelete = false,
  isTeacherAssigned,
  onRequestJoin,
}: SchoolClassCardProps) {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const deleteClass = useSchoolClassStore((s) => s.deleteClass);

  const isAssigned = Boolean(
    isTeacherAssigned ||
      (user?.id &&
        schoolClass.teachers?.some(
          (t) => t.userId === user?.id || t.id === user?.id
        ))
  );

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm(`Are you sure you want to delete class '${schoolClass.name}'?`)) {
      const success = await deleteClass(schoolClass.id);
      if (success) {
        toast.success(`Class '${schoolClass.name}' deleted successfully`);
      } else {
        toast.error("Failed to delete class");
      }
    }
  };

  const handleCopyCode = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (schoolClass.joinCode) {
      navigator.clipboard.writeText(schoolClass.joinCode);
      toast.success(`Copied join code: ${schoolClass.joinCode}`);
    }
  };

  const handleRequestClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onRequestJoin) {
      onRequestJoin(schoolClass.id);
    }
  };

  return (
    <div
      onClick={() => router.push(`${basePath}/${schoolClass.id}`)}
      className="group relative bg-zinc-900 border border-zinc-800 rounded-2xl p-5 shadow-sm hover:border-indigo-500/50 hover:bg-zinc-800/80 hover:-translate-y-0.5 transition-all duration-200 cursor-pointer overflow-hidden flex flex-col justify-between"
    >
      {/* Accent bar on hover */}
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-violet-500 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />

      {/* Header */}
      <div>
        <div className="flex items-start justify-between gap-3 mb-4">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-base font-semibold text-zinc-100">
                {schoolClass.name}
              </h3>
              {isAssigned && (
                <span className="rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-semibold flex items-center gap-1">
                  <Check className="w-3 h-3" /> Already Teaching
                </span>
              )}
            </div>
            <p className="text-xs text-zinc-400 mt-0.5">
              {schoolClass.year && schoolClass.section
                ? `Year: ${schoolClass.year} • Section: ${schoolClass.section}`
                : schoolClass.schoolName || ""}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {schoolClass.joinCode && (
              <button
                type="button"
                onClick={handleCopyCode}
                title="Copy class join code"
                className="flex items-center gap-1.5 font-mono text-xs font-semibold px-2.5 py-1 rounded-full bg-zinc-800 border border-zinc-700 text-indigo-400 hover:bg-zinc-700 hover:text-indigo-300 transition-colors"
              >
                <Copy className="w-3 h-3" />
                <span>{schoolClass.joinCode}</span>
              </button>
            )}
            <span className="shrink-0 text-xs bg-indigo-950/60 text-indigo-300 font-medium px-2.5 py-1 rounded-full border border-indigo-500/30">
              {schoolClass.teachers?.length ?? 0} teacher
              {schoolClass.teachers?.length !== 1 ? "s" : ""}
            </span>
            {showDelete && (
              <button
                type="button"
                onClick={handleDelete}
                title="Delete class"
                className="p-1 text-zinc-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Teachers list */}
        {schoolClass.teachers && schoolClass.teachers.length > 0 ? (
          <div className="space-y-2">
            {schoolClass.teachers.map((teacher) => (
              <div
                key={teacher.id}
                className="flex items-center justify-between rounded-lg bg-zinc-800/70 px-3 py-2 text-sm"
              >
                <div>
                  <p className="font-medium text-zinc-200">{teacher.name}</p>
                  <p className="text-xs text-zinc-400">{teacher.department}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-zinc-400">
                    {Array.isArray(teacher.subjects) && teacher.subjects.length > 0
                      ? teacher.subjects.join(", ")
                      : teacher.department || "Faculty"}
                  </p>
                  <p className="text-xs text-zinc-400">
                    {teacher.experience ?? 0} yrs exp
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-zinc-400">No teachers assigned</p>
        )}
      </div>

      {/* Footer & Action */}
      <div className="mt-4 pt-3 border-t border-zinc-800 flex items-center justify-between text-xs text-zinc-400 gap-2">
        <span>
          Created {formatDateIST(schoolClass.createdAt)}
        </span>
        {isAssigned ? (
          <span className="px-2.5 py-1 rounded-lg bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-semibold text-[11px] inline-flex items-center gap-1.5">
            <Check className="w-3.5 h-3.5" /> Already Teaching This Class
          </span>
        ) : onRequestJoin ? (
          <button
            type="button"
            onClick={handleRequestClick}
            className="px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs transition-colors"
          >
            Request to Teach
          </button>
        ) : (
          <span>
            Updated {formatDateIST(schoolClass.updatedAt)}
          </span>
        )}
      </div>
    </div>
  );
}
