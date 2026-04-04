
import Link from "next/link";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Calendar, Clock, FileText, CheckCircle2, Circle } from "lucide-react";
import type { Exam } from "@/types";

interface ExamCardProps {
  exam: Exam;
}

export function ExamCard({ exam }: ExamCardProps) {
  const formattedDate = new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(exam.scheduledAt));

  return (
    <Link href={`/teacher/exams/${exam.id}`}>
      <GlassCard interactive padding="lg" className="h-full flex flex-col group relative overflow-hidden">
        {/* Decorative background glow for published exams */}
        {exam.isPublished && (
          <div className="absolute -top-10 -right-10 w-40 h-40 bg-emerald-500/10 rounded-full blur-[40px] pointer-events-none" />
        )}

        <div className="flex justify-between items-start mb-4">
          <div className="flex flex-wrap gap-2">
            <Badge variant="default">{exam.type}</Badge>
            {exam.subject && (
              <Badge variant="neutral">{exam.subject.replace("_", " ")}</Badge>
            )}
          </div>
          {exam.isPublished ? (
            <Badge variant="success" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Published
            </Badge>
          ) : (
            <Badge variant="warning" className="bg-amber-500/10 text-amber-400 border-amber-500/20">
              <Circle className="w-3.5 h-3.5 mr-1" /> Draft
            </Badge>
          )}
        </div>

        <h3 className="text-xl font-semibold text-[var(--text-primary)] mb-2 line-clamp-1 group-hover:text-white transition-colors">
          {exam.name}
        </h3>

        <p className="text-sm text-[var(--text-muted)] line-clamp-2 mb-6 flex-grow">
          {exam.description}
        </p>

        <div className="grid grid-cols-2 gap-y-3 gap-x-2 text-sm text-[var(--text-dimmed)]">
          <div className="flex items-center gap-1.5">
            <Calendar className="w-4 h-4 text-[var(--accent)]" />
            <span className="truncate">{formattedDate}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-violet-400" />
            <span>{exam.duration} mins</span>
          </div>
          <div className="flex items-center gap-1.5">
            <FileText className="w-4 h-4 text-emerald-400" />
            <span>{exam.questions?.length ?? 0} Questions</span>
          </div>
          <div className="flex items-center gap-1.5 font-medium">
            <span className="bg-[var(--surface-3)] px-2 py-0.5 rounded-md text-[var(--text-secondary)]">
              {exam.maxMarks} Marks
            </span>
          </div>
        </div>
      </GlassCard>
    </Link>
  );
}
