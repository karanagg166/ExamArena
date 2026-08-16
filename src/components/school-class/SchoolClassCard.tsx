import type { SchoolClass } from "@/types/index";
import { useRouter } from "next/navigation";
import { Copy, Trash2 } from "lucide-react";
import { useSchoolClassStore } from "@/stores";
import { toast } from "sonner";

interface SchoolClassCardProps {
  schoolClass: SchoolClass;
}

export default function SchoolClassCard({ schoolClass }: SchoolClassCardProps) {
  const router = useRouter();
  const deleteClass = useSchoolClassStore((s) => s.deleteClass);

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

  return (
    <div
      onClick={() => router.push(`/principal/school/classes/${schoolClass.id}`)}
      className="group relative bg-zinc-900 border border-zinc-800 rounded-2xl p-5 shadow-sm hover:border-indigo-500/50 hover:bg-zinc-800/80 hover:-translate-y-0.5 transition-all duration-200 cursor-pointer overflow-hidden"
    >
      {/* Accent bar on hover */}
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-violet-500 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />

      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          <h3 className="text-base font-semibold text-zinc-100">
            {schoolClass.name}
          </h3>
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
          <span className="shrink-0 text-xs bg-indigo-50 text-indigo-700 font-medium px-2.5 py-1 rounded-full border border-indigo-100">
            {schoolClass.teachers?.length ?? 0} teacher
            {schoolClass.teachers?.length !== 1 ? "s" : ""}
          </span>
          <button
            type="button"
            onClick={handleDelete}
            title="Delete class"
            className="p-1 text-zinc-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
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

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-zinc-700 flex items-center justify-between text-xs text-zinc-400">
        <span>
          Created {new Date(schoolClass.createdAt).toLocaleDateString()}
        </span>
        <span>
          Updated {new Date(schoolClass.updatedAt).toLocaleDateString()}
        </span>
      </div>
    </div>
  );
}
