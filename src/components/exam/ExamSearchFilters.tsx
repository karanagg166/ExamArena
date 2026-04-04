
import { Search, Filter, X } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";

interface FilterState {
  name: string;
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

export function ExamSearchFilters({ filters, setFilters, onClear }: ExamSearchFiltersProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFilters({ ...filters, [name]: value });
  };

  const hasFilters = Object.values(filters).some(v => v !== "");

  return (
    <GlassCard padding="lg" className="sticky top-24 h-fit border-white/5">
      <div className="flex items-center gap-2 mb-6">
        <Filter className="w-5 h-5 text-[var(--accent)]" />
        <h2 className="text-lg font-semibold text-white">Search Filters</h2>
      </div>

      <div className="space-y-5">
        {/* Exam Name Search */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-[var(--text-dimmed)] uppercase tracking-wider">Exam Title</label>
          <div className="relative">
            <Input
              name="name"
              placeholder="Search exams..."
              value={filters.name}
              onChange={handleChange}
              className="pl-9"
            />
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
          </div>
        </div>

        {/* Teacher Search */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-[var(--text-dimmed)] uppercase tracking-wider">Teacher Name</label>
          <Input
            name="teacherName"
            placeholder="Filter by teacher..."
            value={filters.teacherName}
            onChange={handleChange}
          />
        </div>

        {/* School Search */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-[var(--text-dimmed)] uppercase tracking-wider">School / Institution</label>
          <Input
            name="schoolName"
            placeholder="Filter by school..."
            value={filters.schoolName}
            onChange={handleChange}
          />
        </div>

        {/* Exam Type Dropdown */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-[var(--text-dimmed)] uppercase tracking-wider">Assessment Type</label>
          <Select name="type" value={filters.type} onChange={handleChange}>
            <option value="">All Types</option>
            <option value="MIDTERM">Midterm</option>
            <option value="FINAL">Final</option>
            <option value="QUIZ">Quiz</option>
            <option value="ASSIGNMENT">Assignment</option>
            <option value="MOCK">Mock</option>
          </Select>
        </div>

        {/* Subject Dropdown */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-[var(--text-dimmed)] uppercase tracking-wider">Subject</label>
          <Select name="subject" value={filters.subject} onChange={handleChange}>
            <option value="">All Subjects</option>
            <option value="MATHS">Maths</option>
            <option value="SCIENCE">Science</option>
            <option value="HISTORY">History</option>
            <option value="LITERATURE">Literature</option>
            <option value="ART">Art</option>
            <option value="MUSIC">Music</option>
            <option value="PHYSICAL_EDUCATION">Physical Education</option>
          </Select>
        </div>

        {/* Clear Filters */}
        {hasFilters && (
          <Button
            variant="outline"
            className="w-full mt-4 bg-white/5 border-white/10 hover:bg-white/10"
            onClick={onClear}
          >
            <X className="w-4 h-4 mr-2" /> Clear All
          </Button>
        )}
      </div>
    </GlassCard>
  );
}
