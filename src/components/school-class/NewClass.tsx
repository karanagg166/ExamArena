// src/components/school-class/NewClass.tsx — accept onClose prop
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

interface Props {
  onClose?: () => void;
}

export const NewClass = ({ onClose }: Props) => {
  const [year, setYear] = useState("");
  const [section, setSection] = useState("A");

  const { createClass, loading, error } = useSchoolClassStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!year.trim()) return;

    const name = `${year.trim()} - ${section.trim()}`;
    console.log("Submitting new class:", { name, year, section });

    const success = await createClass({
      name,
      year: year.trim(),
      section: section.trim() || "A",
    });
    console.log("Create class success:", success);
    if (success) {
      toast.success("Class created successfully");
      setYear("");
      setSection("A");
      onClose?.();
    } else {
      toast.error("Failed to create class");
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
              <label className="text-sm text-zinc-400 block mb-1">Year / Grade</label>
              <Input
                type="text"
                value={year}
                onChange={(e) => setYear(e.target.value)}
                placeholder="e.g. 12th, 10th, 1st"
                disabled={loading}
              />
            </div>
            <div>
              <label className="text-sm text-zinc-400 block mb-1">Section / Batch</label>
              <Input
                type="text"
                value={section}
                onChange={(e) => setSection(e.target.value)}
                placeholder="e.g. A, B, C"
                disabled={loading}
              />
            </div>
          </div>
          <FormMessage message={error} type="error" />
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
