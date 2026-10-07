"use client";

import React from "react";
import { CourseMaterialsQA } from "@/components/course-materials/CourseMaterialsQA";

export default function CourseMaterialsPage() {
  return (
    <div className="page-shell">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Course Materials
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Explore and ask questions grounded in your school&apos;s prescribed course materials and textbooks.
          </p>
        </div>

        <CourseMaterialsQA allowSubjectSelect={true} />
      </div>
    </div>
  );
}
