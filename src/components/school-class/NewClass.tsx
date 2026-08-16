"use client";
import React, { useState } from "react";
import { useSchoolClassStore } from "@/stores/index";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { FormMessage } from "@/components/ui/form-message";
import { Input } from "@/components/ui/input";
import { blockNonDigits, sanitizeNumber } from "@/lib/utils";
import { CheckCircle2, Copy, PlusCircle, Users } from "lucide-react";
import type { SchoolClass } from "@/types";

interface Props {
  onClose?: () => void;
}

export const NewClass = ({ onClose }: Props) => {
  const [year, setYear] = useState("");
  const [section, setSection] = useState("A");
  const [localError, setLocalError] = useState("");
  const [createdClass, setCreatedClass] = useState<SchoolClass | null>(null);

  const { classes, createClass, loading, error } = useSchoolClassStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError("");
    if (!year.trim()) return;

    const formattedYear = year.trim();
    const formattedSection = section.trim() || "A";
    const name = `${formattedYear} - ${formattedSection}`;

    // Pre-check duplicate class client-side
    const duplicate = classes.some(
      (c) =>
        c.name.toLowerCase() === name.toLowerCase() ||
        (c.year === formattedYear &&
          c.section?.toLowerCase() === formattedSection.toLowerCase()),
    );

    if (duplicate) {
      const msg = `Class '${name}' already exists of same name.`;
      setLocalError(msg);
      toast.error(msg);
      return;
    }

    const result = await createClass({
      name,
      year: formattedYear,
      section: formattedSection,
    });

    if (result.success && result.data) {
      toast.success("Class created successfully!");
      setCreatedClass(result.data);
    } else if (result.success) {
      toast.success("Class created successfully!");
      onClose?.();
    } else {
      const msg = result.error || `Class '${name}' already exists of same name.`;
      setLocalError(msg);
      toast.error(msg);
    }
  };

  const handleCopyCode = () => {
    if (createdClass?.joinCode) {
      navigator.clipboard.writeText(createdClass.joinCode);
      toast.success(`Copied join code: ${createdClass.joinCode}`);
    }
  };

  const handleResetForAnother = () => {
    setCreatedClass(null);
    setYear("");
    setSection("A");
    setLocalError("");
  };

  if (createdClass) {
    return (
      <Card className="w-full max-w-xl border-emerald-500/30 bg-zinc-950/80">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10 mb-2">
            <CheckCircle2 className="h-6 w-6 text-emerald-400" />
          </div>
          <CardTitle className="text-xl text-white">Class Created Successfully!</CardTitle>
          <CardDescription className="text-zinc-400">
            {createdClass.name} has been added to your school directory.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6 pt-2">
          {/* Join Code Display Banner */}
          <div className="rounded-2xl border border-indigo-500/30 bg-indigo-950/30 p-5 text-center space-y-3">
            <p className="text-xs font-bold uppercase tracking-widest text-indigo-300">
              Student Class Join Code
            </p>
            <div className="flex items-center justify-center gap-3">
              <span className="font-mono text-3xl font-extrabold tracking-[0.25em] text-white">
                {createdClass.joinCode}
              </span>
            </div>
            <p className="text-xs text-zinc-400 max-w-md mx-auto">
              Share this code with your students. When they enter it, their request will arrive in your class approval queue.
            </p>
            <div className="pt-1">
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopyCode}
                className="bg-indigo-600/20 border-indigo-500/40 text-indigo-200 hover:bg-indigo-600/30"
              >
                <Copy className="mr-2 h-4 w-4" /> Copy Join Code
              </Button>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            <Button
              className="w-full"
              onClick={() => onClose?.()}
            >
              <Users className="mr-2 h-4 w-4" /> View Classes
            </Button>
            <Button
              variant="secondary"
              className="w-full"
              onClick={handleResetForAnother}
            >
              <PlusCircle className="mr-2 h-4 w-4" /> Create Another Class
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-xl">
      <CardHeader>
        <CardTitle>Create New Class</CardTitle>
        <CardDescription>
          Add a class under your current school.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-zinc-400 block mb-1">
                Year / Grade (Numbers Only)
              </label>
              <Input
                type="text"
                inputMode="numeric"
                value={year}
                onKeyDown={blockNonDigits}
                onChange={(e) => setYear(sanitizeNumber(e.target.value))}
                placeholder="e.g. 10, 12, 1"
                disabled={loading}
                required
              />
            </div>
            <div>
              <label className="text-sm text-zinc-400 block mb-1">
                Section / Batch
              </label>
              <Input
                type="text"
                value={section}
                onChange={(e) => setSection(e.target.value)}
                placeholder="e.g. A, B, C"
                disabled={loading}
              />
            </div>
          </div>

          <FormMessage message={localError || error} type="error" />

          <div className="flex flex-wrap gap-2">
            <Button type="submit" disabled={loading || !year.trim()}>
              {loading ? "Creating..." : "Create Class"}
            </Button>
            {onClose && (
              <Button type="button" variant="secondary" onClick={onClose}>
                Cancel
              </Button>
            )}
          </div>
        </form>
      </CardContent>
    </Card>
  );
};
