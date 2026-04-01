
import Link from "next/link";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Calendar, Clock, FileText, User as UserIcon, School } from "lucide-react";
import type { Exam } from "@/types";

interface ExamPublicCardProps {
  exam: Exam;
}

export function ExamPublicCard({ exam }: ExamPublicCardProps) {
  const formattedDate = new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(exam.scheduledAt));

  return (
    <Link href={`/exams/${exam.id}`}>
      <GlassCard interactive padding="lg" className="h-full flex flex-col group relative overflow-hidden">
        {/* Top Accent Bar */}
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-[var(--accent)] to-violet-500 opacity-50 transition-opacity group-hover:opacity-100" />

        <div className="flex justify-between items-start mb-4">
          <div className="flex flex-wrap gap-2">
            <Badge variant="default">{exam.type}</Badge>
            {exam.subject && (
              <Badge variant="neutral">{exam.subject.replace("_", " ")}</Badge>
            )}
          </div>
          <div className="text-xs font-medium text-[var(--accent)] bg-[var(--accent)]/10 px-2 py-1 rounded-full border border-[var(--accent)]/20">
            {exam.maxMarks} Marks
          </div>
        </div>

        <h3 className="text-xl font-bold text-[var(--text-primary)] mb-4 line-clamp-1 group-hover:text-white transition-colors">
          {exam.name}
        </h3>

        {/* Teacher & School Info */}
        <div className="space-y-3 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-violet-500/20 flex items-center justify-center border border-violet-500/30">
              <UserIcon className="w-4 h-4 text-violet-400" />
            </div>
            <div>
              <p className="text-xs text-[var(--text-dimmed)] uppercase tracking-wider font-semibold">Teacher</p>
              <p className="text-sm font-medium text-[var(--text-secondary)]">{exam.teacher?.user.name || "Unknown Teacher"}</p>
            </div>
          </div>

          {exam.teacher?.school && (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center border border-emerald-500/30">
                <School className="w-4 h-4 text-emerald-400" />
              </div>
              <div>
                <p className="text-xs text-[var(--text-dimmed)] uppercase tracking-wider font-semibold">School</p>
                <p className="text-sm font-medium text-[var(--text-secondary)]">{exam.teacher.school.name}</p>
              </div>
            </div>
          )}
        </div>

        <div className="mt-auto pt-4 border-t border-white/5 grid grid-cols-2 gap-3 text-sm text-[var(--text-dimmed)]">
          <div className="flex items-center gap-1.5 min-w-0">
            <Calendar className="w-4 h-4 text-[var(--accent)] shrink-0" />
            <span className="truncate">{formattedDate}</span>
          </div>
          <div className="flex items-center gap-1.5 justify-end">
            <Clock className="w-4 h-4 text-violet-400 shrink-0" />
            <span>{exam.duration}m</span>
          </div>
        </div>
      </GlassCard>
    </Link>
  );
}
