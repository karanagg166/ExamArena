"use client";

import React, { useState } from "react";
import { FolderCog, HelpCircle } from "lucide-react";
import { CourseMaterialsQA } from "@/components/course-materials/CourseMaterialsQA";
import { CourseMaterialsManager } from "@/components/course-materials/CourseMaterialsManager";
import { useAuthStore } from "@/stores";

export default function CourseMaterialsPage() {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"qa" | "manage">("qa");

  const canManage =
    user?.role === "TEACHER" ||
    user?.role === "PRINCIPAL" ||
    user?.role === "ADMIN";

  return (
    <div className="page-shell">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Course Materials
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Explore, manage, and ask questions grounded in your school&apos;s prescribed course materials and textbooks.
          </p>
        </div>

        {canManage ? (
          <div className="space-y-6">
            {/* Tab navigation */}
            <div className="flex border-b border-border">
              <button
                onClick={() => setActiveTab("qa")}
                className={`flex items-center gap-2 pb-3 px-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === "qa"
                    ? "border-indigo-500 text-indigo-400"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <HelpCircle className="h-4 w-4" />
                <span>Ask Assistant</span>
              </button>
              <button
                onClick={() => setActiveTab("manage")}
                className={`flex items-center gap-2 pb-3 px-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === "manage"
                    ? "border-indigo-500 text-indigo-400"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <FolderCog className="h-4 w-4" />
                <span>Manage Documents</span>
              </button>
            </div>

            {/* Tab Contents */}
            {activeTab === "qa" ? (
              <CourseMaterialsQA allowSubjectSelect={true} />
            ) : (
              <CourseMaterialsManager />
            )}
          </div>
        ) : (
          <CourseMaterialsQA allowSubjectSelect={true} />
        )}
      </div>
    </div>
  );
}
