"use client";

import React, { useState } from "react";
import { BookOpen, Search, AlertCircle, FileText, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/loading";
import { askCourseMaterials } from "@/lib/api/course-materials";
import type { GroundedAnswer } from "@/types/course-materials";
import { getErrorMessage } from "@/lib/error";
import type { AxiosError } from "axios";

export interface CourseMaterialsQAProps {
  defaultSubject?: string;
  classId?: string;
  allowSubjectSelect?: boolean;
}

const AVAILABLE_SUBJECTS = [
  { value: "SCIENCE", label: "Science (Physics, Chemistry, Biology)" },
  { value: "MATHS", label: "Mathematics" },
  { value: "LITERATURE", label: "Literature / English" },
  { value: "HISTORY", label: "History & Social Studies" },
  { value: "ART", label: "Art" },
  { value: "MUSIC", label: "Music" },
  { value: "PHYSICAL_EDUCATION", label: "Physical Education" },
  { value: "OTHER", label: "Other Materials" },
];

export function CourseMaterialsQA({
  defaultSubject = "SCIENCE",
  classId,
  allowSubjectSelect = true,
}: CourseMaterialsQAProps) {
  const [query, setQuery] = useState("");
  const [subject, setSubject] = useState(defaultSubject);
  const [loading, setLoading] = useState(false);
  const [answerData, setAnswerData] = useState<GroundedAnswer | null>(null);
  const [errorType, setErrorType] = useState<
    "unauthorized" | "unavailable" | "generic" | null
  >(null);
  const [errorDetails, setErrorDetails] = useState<string | null>(null);

  const isNoEvidence =
    Boolean(answerData) &&
    (answerData?.citations.length === 0 ||
      answerData?.answer.toLowerCase().includes("couldn't find") ||
      answerData?.answer
        .toLowerCase()
        .includes("not contain enough information"));

  const handleAsk = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanQuery = query.trim();
    if (!cleanQuery) return;

    setLoading(true);
    setErrorType(null);
    setErrorDetails(null);
    setAnswerData(null);

    try {
      const res = await askCourseMaterials({
        query: cleanQuery,
        subject,
        classId: classId || undefined,
      });
      setAnswerData(res);
    } catch (err: unknown) {
      const axiosErr = err as AxiosError<{ detail?: string }>;
      const statusCode = axiosErr.response?.status;
      if (statusCode === 403) {
        setErrorType("unauthorized");
        setErrorDetails(
          axiosErr.response?.data?.detail ||
            "You are not authorized to access course materials for this scope.",
        );
      } else if (statusCode === 502 || statusCode === 503) {
        setErrorType("unavailable");
        setErrorDetails(
          "Course material search service is temporarily unavailable. Please try again later.",
        );
      } else {
        setErrorType("generic");
        setErrorDetails(getErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="border border-border/80 shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-indigo-500" />
          <CardTitle className="text-lg font-semibold">
            Ask about these materials
          </CardTitle>
        </div>
        <p className="text-xs text-muted-foreground">
          Ask questions grounded in the prescribed syllabus and uploaded course
          materials.
        </p>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Subject selector if enabled */}
        {allowSubjectSelect && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-muted-foreground font-medium">Subject:</span>
            <select
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="rounded-md border border-input bg-background px-2.5 py-1 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-indigo-500"
              aria-label="Select Subject"
            >
              {AVAILABLE_SUBJECTS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Input & Ask Form */}
        <form onSubmit={handleAsk} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="text"
              placeholder="e.g. Explain Newton's second law from our class notes"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
              className="pl-9 text-sm"
              aria-label="Question about course materials"
            />
          </div>
          <Button
            type="submit"
            disabled={loading || !query.trim()}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs sm:text-sm px-4"
          >
            {loading ? (
              <span className="flex items-center gap-1.5">
                <Spinner className="h-3.5 w-3.5" />
                <span>Searching...</span>
              </span>
            ) : (
              "Ask"
            )}
          </Button>
        </form>

        {/* Loading State */}
        {loading && (
          <div
            data-testid="loading-state"
            className="rounded-lg border border-indigo-500/20 bg-indigo-500/5 p-4 flex items-center justify-center gap-2.5 text-sm text-indigo-400 font-medium"
          >
            <Spinner className="h-4 w-4" />
            <span>Searching course materials...</span>
          </div>
        )}

        {/* Authorization Error State */}
        {errorType === "unauthorized" && (
          <div
            data-testid="unauthorized-state"
            className="rounded-lg border border-red-500/30 bg-red-500/10 p-3.5 flex items-start gap-3 text-red-300 text-xs sm:text-sm"
          >
            <AlertCircle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-red-200">Access Restricted</p>
              <p className="mt-0.5 text-red-300/90">{errorDetails}</p>
            </div>
          </div>
        )}

        {/* Provider Unavailable State */}
        {errorType === "unavailable" && (
          <div
            data-testid="unavailable-state"
            className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3.5 flex items-start gap-3 text-amber-300 text-xs sm:text-sm"
          >
            <AlertCircle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-amber-200">Service Unavailable</p>
              <p className="mt-0.5 text-amber-300/90">{errorDetails}</p>
            </div>
          </div>
        )}

        {/* Generic Error State */}
        {errorType === "generic" && (
          <div
            data-testid="generic-error-state"
            className="rounded-lg border border-red-500/30 bg-red-500/10 p-3.5 flex items-start gap-3 text-red-300 text-xs sm:text-sm"
          >
            <AlertCircle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-red-200">Request Error</p>
              <p className="mt-0.5 text-red-300/90">{errorDetails}</p>
            </div>
          </div>
        )}

        {/* No Evidence State */}
        {!loading && isNoEvidence && answerData && (
          <div
            data-testid="no-evidence-state"
            className="rounded-lg border border-zinc-700/60 bg-zinc-800/30 p-4 space-y-2"
          >
            <div className="flex items-center gap-2 text-zinc-300 font-medium text-sm">
              <AlertCircle className="h-4 w-4 text-amber-400 shrink-0" />
              <span>Insufficient Evidence</span>
            </div>
            <p className="text-xs sm:text-sm text-zinc-400 leading-relaxed">
              {answerData.answer}
            </p>
          </div>
        )}

        {/* Success Answer State (with citations) */}
        {!loading && answerData && !isNoEvidence && (
          <div data-testid="answer-state" className="space-y-4 pt-1">
            <div className="rounded-lg border border-border bg-card/60 p-4 space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-indigo-400">
                <Sparkles className="h-3.5 w-3.5" />
                <span>Answer:</span>
              </div>
              <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                {answerData.answer}
              </p>
            </div>

            {/* Citations List */}
            {answerData.citations.length > 0 && (
              <div data-testid="citations-state" className="space-y-2.5">
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                  <FileText className="h-3.5 w-3.5" />
                  <span>Sources</span>
                </h4>
                <div className="space-y-2">
                  {answerData.citations.map((c) => (
                    <div
                      key={c.citationNumber}
                      data-testid={`citation-${c.citationNumber}`}
                      className="rounded-md border border-border/80 bg-muted/40 p-3 text-xs space-y-1"
                    >
                      <div className="flex items-baseline justify-between gap-2">
                        <p className="font-semibold text-indigo-400">
                          [{c.citationNumber}]{" "}
                          <span className="text-foreground">
                            {c.title || c.fileName || "Course Document"}
                          </span>
                        </p>
                        {c.pageNumber != null && (
                          <span className="text-[11px] text-muted-foreground shrink-0 font-medium">
                            Page {c.pageNumber}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground italic pl-2 border-l-2 border-indigo-500/40">
                        &ldquo;{c.textSnippet}&rdquo;
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
