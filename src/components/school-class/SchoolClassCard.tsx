import type { SchoolClass } from "@/types/index";
import { useRouter } from "next/navigation";

interface SchoolClassCardProps {
    schoolClass: SchoolClass;
}

export default function SchoolClassCard({ schoolClass }: SchoolClassCardProps) {
    const router = useRouter();

    return (
        <div
            onClick={() => router.push(`/school/${schoolClass.schoolId}/school-class/${schoolClass.id}`)}
            className="group relative bg-zinc-900 border border-zinc-800 rounded-2xl p-5 shadow-sm hover:border-indigo-500/50 hover:bg-zinc-800/80 hover:-translate-y-0.5 transition-all duration-200 cursor-pointer overflow-hidden"
        >
            {/* Accent bar on hover */}
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-violet-500 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />

            {/* Header */}
            <div className="flex items-start justify-between gap-3 mb-4">
                <div>
                    <h3 className="text-base font-semibold text-gray-900">{schoolClass.name}</h3>
                    {schoolClass.schoolName && (
                        <p className="text-xs text-gray-400 mt-0.5">{schoolClass.schoolName}</p>
                    )}
                </div>
                <span className="shrink-0 text-xs bg-indigo-50 text-indigo-700 font-medium px-2.5 py-1 rounded-full border border-indigo-100">
                    {schoolClass.teachers?.length ?? 0} teacher{schoolClass.teachers?.length !== 1 ? "s" : ""}
                </span>
            </div>

            {/* Teachers list */}
            {schoolClass.teachers && schoolClass.teachers.length > 0 ? (
                <div className="space-y-2">
                    {schoolClass.teachers.map((teacher) => (
                        <div
                            key={teacher.id}
                            className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-sm"
                        >
                            <div>
                                <p className="font-medium text-gray-800">{teacher.name}</p>
                                <p className="text-xs text-gray-400">{teacher.department}</p>
                            </div>
                            <div className="text-right">
                                <p className="text-xs text-gray-400">{teacher.subjects.join(", ")}</p>
                                <p className="text-xs text-gray-400">{teacher.experience} yrs exp</p>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <p className="text-xs text-gray-400">No teachers assigned</p>
            )}

            {/* Footer */}
            <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-400">
                <span>Created {new Date(schoolClass.createdAt).toLocaleDateString()}</span>
                <span>Updated {new Date(schoolClass.updatedAt).toLocaleDateString()}</span>
            </div>
        </div>
    );
}