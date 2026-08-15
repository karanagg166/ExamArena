import { useState } from "react";
import {
  Search,
  SlidersHorizontal,
  X,
  Hash,
  User,
  Building2,
  Bookmark,
  BookOpen,
  RotateCcw,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";

export interface FilterState {
  name: string;
  code: string;
  type: string;
  teacherName: string;
  schoolName: string;
  subject: string;
}

interface ExamSearchFiltersProps {
  filters: FilterState;
  setFilters: (filters: FilterState) => void;
  onClear: () => void;
}

export function ExamSearchFilters({
  filters,
  setFilters,
  onClear,
}: ExamSearchFiltersProps) {
  const [isOpenMobile, setIsOpenMobile] = useState(false);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFilters({ ...filters, [name]: value });
  };

  const removeFilter = (key: keyof FilterState) => {
    setFilters({ ...filters, [key]: "" });
  };

  const activeFilterEntries = Object.entries(filters).filter(
    ([, val]) => val.trim() !== ""
  );
  const activeCount = activeFilterEntries.length;
  const hasFilters = activeCount > 0;

  return (
    <GlassCard
      padding="none"
      className="sticky top-20 z-10 overflow-hidden border-white/10 bg-white/[0.03] backdrop-blur-xl shadow-2xl rounded-2xl transition-all duration-300"
    >
      {/* Mobile Toggle Bar */}
      <div className="lg:hidden flex items-center justify-between p-4 bg-white/[0.02] border-b border-white/10">
        <button
          type="button"
          onClick={() => setIsOpenMobile((prev) => !prev)}
          className="flex items-center gap-2.5 text-sm font-semibold text-white focus:outline-none"
        >
          <div className="p-1.5 rounded-lg bg-[var(--accent)]/15 text-[var(--accent)] border border-[var(--accent)]/20">
            <SlidersHorizontal className="w-4 h-4" />
          </div>
          <span>Search & Filter Assessments</span>
          {hasFilters && (
            <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-[var(--accent)] text-white shadow-sm">
              {activeCount}
            </span>
          )}
        </button>

        <div className="flex items-center gap-2">
          {hasFilters && (
            <button
              type="button"
              onClick={onClear}
              className="text-xs font-medium text-red-400 hover:text-red-300 flex items-center gap-1 transition-colors px-2 py-1 rounded-md hover:bg-red-500/10"
            >
              <RotateCcw className="w-3 h-3" /> Clear
            </button>
          )}
          <button
            type="button"
            onClick={() => setIsOpenMobile((prev) => !prev)}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Toggle filters"
          >
            {isOpenMobile ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Main Filter Content */}
      <div
        className={`${
          isOpenMobile ? "block" : "hidden"
        } lg:block p-5 md:p-6 max-h-[calc(100vh-6rem)] overflow-y-auto custom-scrollbar space-y-6`}
      >
        {/* Desktop Header */}
        <div className="hidden lg:flex items-center justify-between pb-4 border-b border-white/10">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-[var(--accent)]/15 text-[var(--accent)] border border-[var(--accent)]/20 shadow-inner">
              <SlidersHorizontal className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-tight">
                Search & Filter
              </h2>
              <p className="text-[11px] text-[var(--text-dimmed)]">
                Refine assessments by criteria
              </p>
            </div>
          </div>

          {hasFilters && (
            <button
              type="button"
              onClick={onClear}
              className="text-xs font-semibold text-red-400 hover:text-red-300 flex items-center gap-1.5 transition-all px-2.5 py-1 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/20"
            >
              <RotateCcw className="w-3 h-3" /> Reset
            </button>
          )}
        </div>

        {/* Active Filter Pills */}
        {hasFilters && (
          <div className="space-y-2 pt-1 pb-2 border-b border-white/5">
            <div className="flex items-center justify-between text-[11px] font-semibold text-[var(--text-dimmed)] uppercase tracking-wider">
              <span>Active Filters ({activeCount})</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {activeFilterEntries.map(([key, val]) => (
                <span
                  key={key}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-[var(--accent)]/10 text-[var(--accent)] border border-[var(--accent)]/25 group"
                >
                  <span className="capitalize">
                    {key === "teacherName"
                      ? "Teacher"
                      : key === "schoolName"
                      ? "School"
                      : key}
                    :
                  </span>
                  <span className="font-semibold text-white">{val}</span>
                  <button
                    type="button"
                    onClick={() => removeFilter(key as keyof FilterState)}
                    className="hover:bg-[var(--accent)]/20 rounded-full p-0.5 transition-colors text-[var(--accent)] group-hover:text-white"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Filter Inputs Grid / Stack */}
        <div className="space-y-4">
          {/* Section 1: Keywords & Code */}
          <div className="space-y-3">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
                <Search className="w-3.5 h-3.5 text-[var(--accent)]" />
                <span>Exam Title</span>
              </label>
              <div className="relative">
                <Input
                  name="name"
                  placeholder="Search exam title..."
                  value={filters.name}
                  onChange={handleChange}
                  className="pl-9 bg-black/20 border-white/10 focus:border-[var(--accent)] focus:ring-[var(--accent)]/20 text-white placeholder:text-zinc-500 rounded-xl"
                />
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400 pointer-events-none" />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
                <Hash className="w-3.5 h-3.5 text-[var(--accent)]" />
                <span>Exam Search Code</span>
              </label>
              <div className="relative">
                <Input
                  name="code"
                  placeholder="e.g. Np008, mock-test1"
                  value={filters.code}
                  onChange={handleChange}
                  className="pl-9 font-mono text-sm bg-black/20 border-white/10 focus:border-[var(--accent)] text-white placeholder:text-zinc-500 rounded-xl"
                />
                <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400 pointer-events-none" />
              </div>
            </div>
          </div>

          {/* Section 2: Dropdowns (Type & Subject) */}
          <div className="space-y-3 pt-2 border-t border-white/5">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
                <Bookmark className="w-3.5 h-3.5 text-[var(--accent)]" />
                <span>Assessment Type</span>
              </label>
              <Select
                name="type"
                value={filters.type}
                onChange={handleChange}
                className="bg-black/20 border-white/10 focus:border-[var(--accent)] text-white rounded-xl"
              >
                <option value="">All Types</option>
                <option value="MIDTERM">Midterm Exam</option>
                <option value="FINAL">Final Exam</option>
                <option value="QUIZ">Quiz / Assessment</option>
                <option value="ASSIGNMENT">Assignment</option>
                <option value="MOCK">Mock Practice</option>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5 text-[var(--accent)]" />
                <span>Subject</span>
              </label>
              <Select
                name="subject"
                value={filters.subject}
                onChange={handleChange}
                className="bg-black/20 border-white/10 focus:border-[var(--accent)] text-white rounded-xl"
              >
                <option value="">All Subjects</option>
                <option value="MATHS">Mathematics</option>
                <option value="SCIENCE">Science</option>
                <option value="HISTORY">History</option>
                <option value="LITERATURE">Literature</option>
                <option value="ART">Art & Design</option>
                <option value="MUSIC">Music</option>
                <option value="PHYSICAL_EDUCATION">Physical Education</option>
              </Select>
            </div>
          </div>

          {/* Section 3: Educator & Institution */}
          <div className="space-y-3 pt-2 border-t border-white/5">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-[var(--accent)]" />
                <span>Teacher / Instructor</span>
              </label>
              <div className="relative">
                <Input
                  name="teacherName"
                  placeholder="Filter by teacher..."
                  value={filters.teacherName}
                  onChange={handleChange}
                  className="pl-9 bg-black/20 border-white/10 focus:border-[var(--accent)] text-white placeholder:text-zinc-500 rounded-xl"
                />
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400 pointer-events-none" />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
                <Building2 className="w-3.5 h-3.5 text-[var(--accent)]" />
                <span>School / Institution</span>
              </label>
              <div className="relative">
                <Input
                  name="schoolName"
                  placeholder="Filter by school..."
                  value={filters.schoolName}
                  onChange={handleChange}
                  className="pl-9 bg-black/20 border-white/10 focus:border-[var(--accent)] text-white placeholder:text-zinc-500 rounded-xl"
                />
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400 pointer-events-none" />
              </div>
            </div>
          </div>

          {/* Clear Button at Bottom */}
          {hasFilters && (
            <div className="pt-2">
              <Button
                variant="outline"
                className="w-full bg-red-500/10 hover:bg-red-500/20 text-red-300 border-red-500/20 hover:border-red-500/40 rounded-xl transition-all flex items-center justify-center gap-2"
                onClick={onClear}
              >
                <X className="w-4 h-4" /> Clear All Filters
              </Button>
            </div>
          )}
        </div>
      </div>
    </GlassCard>
  );
}
