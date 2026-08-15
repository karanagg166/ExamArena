import React from "react";
import { blockNonDigits } from "@/lib/utils";
import { GlassCard } from "@/components/ui/glass-card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import type { ExamType, Subject } from "@/types";

interface ExamFormProps {
  exam: {
    name: string;
    description: string;
    scheduledAt: string;
    duration: number;
    type: ExamType;
    maxMarks: number;
    isPublished: boolean;
    isPublic?: boolean;
    examCode?: string;
    accessPassword?: string;
    negativeMarking?: boolean;
    negativeMarks?: number;
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

  const generateRandomCode = () => {
    const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    let code = "EXM-";
    for (let i = 0; i < 6; i++) {
      code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    onChange({ examCode: code });
  };

  return (
    <GlassCard padding="lg" className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[var(--text-primary)]">
          Exam Details & Settings
        </h2>
        <p className="text-[var(--text-muted)] text-sm mb-6 mt-1">
          Configure title, scheduling, search identifier, privacy password, and marking rules.
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

          {/* Exam Search Code / Identifier */}
          <div className="space-y-1.5 md:col-span-2">
            <Label htmlFor="examCode">Exam Search Code / Identifier</Label>
            <div className="flex gap-2">
              <Input
                id="examCode"
                placeholder="e.g., Np008, mock-test1, chem-term1"
                value={exam.examCode || ""}
                onChange={(e) => onChange({ examCode: e.target.value })}
                className="font-mono"
              />
              <Button type="button" variant="outline" size="sm" onClick={generateRandomCode}>
                Generate Code
              </Button>
            </div>
            <p className="text-[11px] text-[var(--text-muted)]">
              🔍 A quick identifier for your exam. Students can search for this exam using this code or by title (case-insensitive, e.g. &quot;np008&quot; or &quot;mock-test1&quot;).
            </p>
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
            <Label htmlFor="scheduledAt">Scheduled Start Date & Time <span className="text-red-400">*</span></Label>
            <Input
              id="scheduledAt"
              type="datetime-local"
              value={scheduledDateString}
              onChange={handleDateChange}
            />
            <p className="text-[11px] text-[var(--text-muted)]">
              ℹ️ Students can take this exam at any time on or after this scheduled start time.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="duration">Duration (mins) <span className="text-red-400">*</span></Label>
              <Input
                id="duration"
                type="number"
                min="5"
                step="5"
                inputMode="numeric"
                onKeyDown={blockNonDigits}
                value={exam.duration || ""}
                onChange={(e) => onChange({ duration: parseInt(e.target.value) || 0 })}
                error={exam.duration !== undefined && exam.duration < 5 ? "Minimum duration is 5 mins" : undefined}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="maxMarks">Max Marks <span className="text-red-400">*</span></Label>
              <Input
                id="maxMarks"
                type="number"
                min="1"
                inputMode="numeric"
                onKeyDown={blockNonDigits}
                value={exam.maxMarks || ""}
                onChange={(e) => onChange({ maxMarks: parseInt(e.target.value) || 0 })}
                error={exam.maxMarks !== undefined && exam.maxMarks < 1 ? "Max marks must be at least 1" : undefined}
              />
            </div>
          </div>
        </div>

        {/* Privacy, Public Exam & Access Password */}
        <div className="p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-2)]/40 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <Label className="text-sm font-semibold text-[var(--text-primary)]">Exam Visibility & Access</Label>
              <p className="text-xs text-[var(--text-muted)]">
                Choose whether this exam is open to any student in the school, or protected with a secret password.
              </p>
            </div>
            <div className="inline-flex rounded-xl border border-[var(--border-default)] p-1 bg-[var(--surface-1)] shrink-0">
              <Button
                type="button"
                size="sm"
                variant={exam.isPublic !== false ? "secondary" : "ghost"}
                onClick={() => onChange({ isPublic: true })}
              >
                Public Exam
              </Button>
              <Button
                type="button"
                size="sm"
                variant={exam.isPublic === false ? "secondary" : "ghost"}
                onClick={() => onChange({ isPublic: false })}
              >
                Password Protected
              </Button>
            </div>
          </div>

          <p className="text-[11px] text-[var(--text-muted)]">
            💡 Teachers and Principals can switch an exam between Public and Password-Protected at any time in the future.
          </p>

          {exam.isPublic === false && (
            <div className="space-y-2 pt-2 border-t border-[var(--border-subtle)]">
              <Label htmlFor="accessPassword">Exam Access Password / Secret Key</Label>
              <Input
                id="accessPassword"
                type="text"
                placeholder="e.g., SECRET-PASS-123"
                value={exam.accessPassword || ""}
                onChange={(e) => onChange({ accessPassword: e.target.value })}
                className="font-mono tracking-wider"
              />
              <p className="text-xs text-[var(--text-muted)]">
                Students must enter this password to begin the exam.
              </p>
            </div>
          )}
        </div>

        {/* Negative Marking Policy */}
        <div className="p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-2)]/40 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <Label className="text-sm font-semibold text-[var(--text-primary)]">Default Exam Negative Marking</Label>
              <p className="text-xs text-[var(--text-muted)]">
                Default penalty for wrong answers across the exam. Note: you can also configure negative marking individually per Section below!
              </p>
            </div>
            <div className="inline-flex rounded-xl border border-[var(--border-default)] p-1 bg-[var(--surface-1)] shrink-0">
              <Button
                type="button"
                size="sm"
                variant={exam.negativeMarking ? "secondary" : "ghost"}
                onClick={() => onChange({ negativeMarking: true, negativeMarks: exam.negativeMarks || 1.0 })}
              >
                Enabled
              </Button>
              <Button
                type="button"
                size="sm"
                variant={!exam.negativeMarking ? "secondary" : "ghost"}
                onClick={() => onChange({ negativeMarking: false, negativeMarks: 0 })}
              >
                Disabled
              </Button>
            </div>
          </div>

          {exam.negativeMarking && (
            <div className="space-y-2 pt-2 border-t border-[var(--border-subtle)]">
              <Label htmlFor="negativeMarks">Default Deduction per Wrong Answer (Marks)</Label>
              <Input
                id="negativeMarks"
                type="number"
                step="0.25"
                min="0.25"
                placeholder="e.g. 1 or 0.25"
                value={exam.negativeMarks ?? 1.0}
                onChange={(e) => onChange({ negativeMarks: parseFloat(e.target.value) || 0 })}
              />
              <p className="text-xs text-[var(--text-muted)]">
                Sections with their own negative marking settings will override this default.
              </p>
            </div>
          )}
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

        <div className="space-y-2">
          <Label>Publish Status</Label>
          <div className="inline-flex rounded-xl border border-[var(--border-default)] p-1 bg-[var(--surface-1)]">
            <Button
              type="button"
              size="sm"
              variant={exam.isPublished ? "ghost" : "secondary"}
              onClick={() => onChange({ isPublished: false })}
            >
              Draft
            </Button>
            <Button
              type="button"
              size="sm"
              variant={exam.isPublished ? "secondary" : "ghost"}
              onClick={() => onChange({ isPublished: true })}
            >
              Published
            </Button>
          </div>
          <p className="text-xs text-[var(--text-muted)]">
            Draft exams are visible only to you. Published exams are visible to students.
          </p>
        </div>
      </div>
    </GlassCard>
  );
}
