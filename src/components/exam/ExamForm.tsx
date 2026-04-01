import React from "react";
import { GlassCard } from "@/components/ui/glass-card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import type { ExamType, Subject } from "@/types";

interface ExamFormProps {
  exam: {
    name: string;
    description: string;
    scheduledAt: string;
    duration: number;
    type: ExamType;
    maxMarks: number;
    subject?: Subject;
    instructions?: string;
  };
  onChange: (updates: Partial<ExamFormProps["exam"]>) => void;
}

const EXAM_TYPES: { label: string; value: ExamType }[] = [
  { label: "Midterm", value: "MIDTERM" },
  { label: "Final Exam", value: "FINAL" },
  { label: "Quiz", value: "QUIZ" },
  { label: "Assignment", value: "ASSIGNMENT" },
  { label: "Mock Exam", value: "MOCK" },
];

const SUBJECTS: { label: string; value: Subject }[] = [
  { label: "Mathematics", value: "MATHS" },
  { label: "Science", value: "SCIENCE" },
  { label: "History", value: "HISTORY" },
  { label: "Literature", value: "LITERATURE" },
  { label: "Art", value: "ART" },
  { label: "Music", value: "MUSIC" },
  { label: "Physical Education", value: "PHYSICAL_EDUCATION" },
];

export function ExamForm({ exam, onChange }: ExamFormProps) {
  // Convert standard ISO date to datetime-local format if present
  const scheduledDateString = exam.scheduledAt
    ? new Date(exam.scheduledAt).toISOString().slice(0, 16)
    : "";

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.value) {
      onChange({ scheduledAt: "" });
      return;
    }
    // Convert back to full ISO string
    const date = new Date(e.target.value);
    onChange({ scheduledAt: date.toISOString() });
  };

  return (
    <GlassCard padding="lg" className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[var(--text-primary)]">
          Exam Details
        </h2>
        <p className="text-[var(--text-muted)] text-sm mb-6 mt-1">
          Configure the core settings for this assessment.
        </p>
      </div>

      <div className="space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div className="space-y-1.5 md:col-span-2">
            <Label htmlFor="title">Exam Title <span className="text-red-400">*</span></Label>
            <Input
              id="title"
              placeholder="e.g., Midterm: Algebra & Geometry"
              value={exam.name}
              onChange={(e) => onChange({ name: e.target.value })}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="examType">Exam Type <span className="text-red-400">*</span></Label>
            <Select
              id="examType"
              value={exam.type}
              onChange={(e) => onChange({ type: e.target.value as ExamType })}
            >
              <option value="" disabled>Select Type...</option>
              {EXAM_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="subject">Subject</Label>
            <Select
              id="subject"
              value={exam.subject || ""}
              onChange={(e) => onChange({ subject: (e.target.value || undefined) as Subject })}
            >
              <option value="">No Subject Specified</option>
              {SUBJECTS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="scheduledAt">Scheduled Date & Time <span className="text-red-400">*</span></Label>
            <Input
              id="scheduledAt"
              type="datetime-local"
              value={scheduledDateString}
              onChange={handleDateChange}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="duration">Duration (mins) <span className="text-red-400">*</span></Label>
              <Input
                id="duration"
                type="number"
                min="5"
                step="5"
                value={exam.duration || ""}
                onChange={(e) => onChange({ duration: parseInt(e.target.value) || 0 })}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="maxMarks">Max Marks <span className="text-red-400">*</span></Label>
              <Input
                id="maxMarks"
                type="number"
                min="1"
                value={exam.maxMarks || ""}
                onChange={(e) => onChange({ maxMarks: parseInt(e.target.value) || 0 })}
              />
            </div>
          </div>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="description">Short Description <span className="text-red-400">*</span></Label>
          <Textarea
            id="description"
            className="min-h-20"
            placeholder="A brief overview of what this exam evaluates..."
            value={exam.description}
            onChange={(e) => onChange({ description: e.target.value })}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="instructions">Student Instructions</Label>
          <Textarea
            id="instructions"
            placeholder="Any specific rules or instructions for students..."
            value={exam.instructions || ""}
            onChange={(e) => onChange({ instructions: e.target.value })}
          />
        </div>
      </div>
    </GlassCard>
  );
}
