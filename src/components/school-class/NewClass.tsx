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

interface Props {
  onClose?: () => void;
}

export const NewClass = ({ onClose }: Props) => {
  const [year, setYear] = useState("");
  const [section, setSection] = useState("A");
  const [localError, setLocalError] = useState("");

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

    console.log("Submitting new class:", { name, year: formattedYear, section: formattedSection });

    const result = await createClass({
      name,
      year: formattedYear,
      section: formattedSection,
    });

    if (result.success) {
      toast.success("Class created successfully");
      setYear("");
      setSection("A");
      onClose?.();
    } else {
      const msg = result.error || `Class '${name}' already exists of same name.`;
      setLocalError(msg);
      toast.error(msg);
    }
  };

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
