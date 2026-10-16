"use client";

import React, { useState, useMemo } from "react";
import {
  Award,
  Search,
  Download,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/loading";

export interface StudentScoreboardResult {
  rank: number;
  attemptId: string;
  studentId: string;
  studentName: string;
  rollNo: string;
  marksObtained: number;
  maxMarks: number;
  percentage: number;
  status: string;
  startedAt: string;
  submittedAt?: string | null;
}

interface ExamResultsTableProps {
  results: StudentScoreboardResult[];
  maxMarks?: number;
  loading?: boolean;
  onViewAttempt?: (attemptId: string) => void;
  emptyMessage?: string;
}

export function ExamResultsTable({
  results,
  maxMarks,
  loading = false,
  onViewAttempt,
  emptyMessage = "No student attempt results found.",
}: ExamResultsTableProps) {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<
    "ALL" | "PASSED" | "FAILED" | "DISTINCTION"
  >("ALL");
  const [sortBy, setSortBy] = useState<
    "RANK_ASC" | "SCORE_DESC" | "SCORE_ASC" | "NAME_ASC"
  >("RANK_ASC");

  const filteredResults = useMemo(() => {
    let list = [...results];

    // Search query filter
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (r) =>
          r.studentName.toLowerCase().includes(q) ||
          r.rollNo.toLowerCase().includes(q)
      );
    }

    // Performance Bracket Filter
    if (statusFilter === "PASSED") {
      list = list.filter((r) => r.percentage >= 40);
    } else if (statusFilter === "FAILED") {
      list = list.filter((r) => r.percentage < 40);
    } else if (statusFilter === "DISTINCTION") {
      list = list.filter((r) => r.percentage >= 80);
    }

    // Sorting
    list.sort((a, b) => {
      switch (sortBy) {
        case "SCORE_DESC":
          return b.marksObtained - a.marksObtained;
        case "SCORE_ASC":
          return a.marksObtained - b.marksObtained;
        case "NAME_ASC":
          return a.studentName.localeCompare(b.studentName);
        case "RANK_ASC":
        default:
          return a.rank - b.rank;
      }
    });

    return list;
  }, [results, search, statusFilter, sortBy]);

  const handleExportCSV = () => {
    if (!results.length) return;
    const headers = [
      "Rank",
      "Student Name",
      "Roll No",
      "Marks Obtained",
      "Max Marks",
      "Percentage",
      "Status",
      "Submitted At",
    ];
    const rows = filteredResults.map((r) => [
      r.rank,
      `"${r.studentName.replace(/"/g, '""')}"`,
      r.rollNo,
      r.marksObtained,
      r.maxMarks || maxMarks || 100,
      `${r.percentage.toFixed(1)}%`,
      r.status,
      r.submittedAt ? new Date(r.submittedAt).toLocaleString() : "In Progress",
    ]);

    const csvContent = [headers.join(","), ...rows.map((row) => row.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `exam_results_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-4">
      {/* Control bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search candidates by name or roll number..."
            className="w-full pl-10 pr-4 py-2 text-sm rounded-xl border border-zinc-800 bg-zinc-950/60 text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <select
            value={statusFilter}
            onChange={(e) =>
              setStatusFilter(
                e.target.value as "ALL" | "PASSED" | "FAILED" | "DISTINCTION"
              )
            }
            className="px-3 py-2 text-xs rounded-xl border border-zinc-800 bg-zinc-950/60 text-zinc-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="ALL">All Scores ({results.length})</option>
            <option value="DISTINCTION">Distinction (≥ 80%)</option>
            <option value="PASSED">Passed (≥ 40%)</option>
            <option value="FAILED">Failed (&lt; 40%)</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) =>
              setSortBy(
                e.target.value as
                  | "RANK_ASC"
                  | "SCORE_DESC"
                  | "SCORE_ASC"
                  | "NAME_ASC"
              )
            }
            className="px-3 py-2 text-xs rounded-xl border border-zinc-800 bg-zinc-950/60 text-zinc-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="RANK_ASC">Sort: Rank (1 → N)</option>
            <option value="SCORE_DESC">Sort: Highest Score</option>
            <option value="SCORE_ASC">Sort: Lowest Score</option>
            <option value="NAME_ASC">Sort: Student Name</option>
          </select>

          {results.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportCSV}
              className="text-xs border-zinc-800 hover:bg-zinc-800"
            >
              <Download className="mr-1.5 h-3.5 w-3.5" />
              Export CSV
            </Button>
          )}
        </div>
      </div>

      {/* Table Content */}
      {loading ? (
        <div className="flex min-h-[220px] flex-col items-center justify-center gap-3 rounded-2xl border border-zinc-800 bg-zinc-950/40 p-8">
          <Spinner className="h-7 w-7 text-indigo-500" />
          <p className="text-xs text-zinc-400">Loading student scores...</p>
        </div>
      ) : filteredResults.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-zinc-800 bg-zinc-950/30 p-10 text-center">
          <p className="text-sm text-zinc-400">{emptyMessage}</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-zinc-800 bg-zinc-950/40 shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-zinc-800 bg-zinc-900/60 text-xs uppercase tracking-wider text-zinc-400 font-semibold">
              <tr>
                <th className="px-5 py-3.5">Rank</th>
                <th className="px-5 py-3.5">Student</th>
                <th className="px-5 py-3.5">Roll Number</th>
                <th className="px-5 py-3.5">Score</th>
                <th className="px-5 py-3.5">Performance</th>
                <th className="px-5 py-3.5">Status</th>
                {onViewAttempt && <th className="px-5 py-3.5 text-right">Action</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {filteredResults.map((r) => {
                return (
                  <tr
                    key={r.attemptId}
                    className="hover:bg-zinc-900/30 transition-colors"
                  >
                    <td className="px-5 py-4 font-mono font-bold">
                      {r.rank === 1 ? (
                        <span className="flex items-center gap-1.5 text-amber-400">
                          <Award className="h-4 w-4" /> 1st
                        </span>
                      ) : r.rank === 2 ? (
                        <span className="flex items-center gap-1.5 text-slate-300">
                          <Award className="h-4 w-4" /> 2nd
                        </span>
                      ) : r.rank === 3 ? (
                        <span className="flex items-center gap-1.5 text-amber-600">
                          <Award className="h-4 w-4" /> 3rd
                        </span>
                      ) : (
                        <span className="text-zinc-400">#{r.rank}</span>
                      )}
                    </td>

                    <td className="px-5 py-4">
                      <div className="font-semibold text-white">{r.studentName}</div>
                    </td>

                    <td className="px-5 py-4 font-mono text-xs text-zinc-400">
                      {r.rollNo || "—"}
                    </td>

                    <td className="px-5 py-4">
                      <div className="font-semibold text-white font-mono">
                        {r.marksObtained}
                        <span className="text-xs text-zinc-500 font-normal">
                          {" "}
                          / {r.maxMarks || maxMarks || 100}
                        </span>
                      </div>
                    </td>

                    <td className="px-5 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              r.percentage >= 80
                                ? "bg-emerald-500"
                                : r.percentage >= 40
                                ? "bg-indigo-500"
                                : "bg-rose-500"
                            }`}
                            style={{ width: `${Math.min(100, Math.max(0, r.percentage))}%` }}
                          />
                        </div>
                        <span className="text-xs font-mono text-zinc-300">
                          {r.percentage.toFixed(1)}%
                        </span>
                      </div>
                    </td>

                    <td className="px-5 py-4">
                      {r.status === "SUBMITTED" || r.status === "EVALUATED" ? (
                        <Badge
                          variant="secondary"
                          className={
                            r.percentage >= 40
                              ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
                              : "bg-rose-500/15 text-rose-400 border-rose-500/30"
                          }
                        >
                          {r.percentage >= 40 ? "Passed" : "Failed"}
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-zinc-400">
                          {r.status}
                        </Badge>
                      )}
                    </td>

                    {onViewAttempt && (
                      <td className="px-5 py-4 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onViewAttempt(r.attemptId)}
                          className="h-8 text-xs text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10"
                        >
                          Review <ChevronRight className="ml-1 h-3.5 w-3.5" />
                        </Button>
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default ExamResultsTable;
