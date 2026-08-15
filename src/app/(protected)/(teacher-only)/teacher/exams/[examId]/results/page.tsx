"use client";

import React, { useEffect, useState, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Award,
  Search,
  Users,
  TrendingUp,
  Download,
  Calendar,
  CheckCircle2,
  Clock,
  ChevronRight,
} from "lucide-react";

import { PageHeader } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/loading";
import { api } from "@/lib/axios";
import type { Exam } from "@/types";

interface StudentScoreboardResult {
  rank: number;
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

export default function ExamResultsLeaderboardPage() {
  const { examId } = useParams<{ examId: string }>();
  const router = useRouter();

  const [exam, setExam] = useState<Exam | null>(null);
  const [results, setResults] = useState<StudentScoreboardResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const fetchExamAndResults = async () => {
      setLoading(true);
      setError(null);
      try {
        const [examRes, resultsRes] = await Promise.all([
          api.get<Exam>(`/api/v1/exams/${examId}`),
          api.get<StudentScoreboardResult[]>(`/api/v1/exams/${examId}/results`),
        ]);
        setExam(examRes.data);
        setResults(resultsRes.data);
      } catch (err: unknown) {
        const detail =
          (err as { response?: { data?: { detail?: string } } })?.response
            ?.data?.detail;
        setError(detail ?? "Failed to load exam results.");
      } finally {
        setLoading(false);
      }
    };

    if (examId) fetchExamAndResults();
  }, [examId]);

  const filteredResults = useMemo(() => {
    if (!search.trim()) return results;
    const q = search.toLowerCase();
    return results.filter(
      (r) =>
        r.studentName.toLowerCase().includes(q) ||
        r.rollNo.toLowerCase().includes(q),
    );
  }, [results, search]);

  const stats = useMemo(() => {
    if (results.length === 0) {
      return { total: 0, avg: 0, highest: 0, passRate: 0 };
    }
    const total = results.length;
    const totalMarksSum = results.reduce((acc, curr) => acc + curr.marksObtained, 0);
    const avg = Math.round(totalMarksSum / total);
    const highest = Math.max(...results.map((r) => r.marksObtained));
    const passed = results.filter((r) => r.percentage >= 40).length;
    const passRate = Math.round((passed / total) * 100);
    return { total, avg, highest, passRate };
  }, [results]);

  const handleExportCSV = () => {
    if (results.length === 0) return;
    const headers = ["Rank,Student Name,Roll Number,Marks Obtained,Max Marks,Percentage,Status\n"];
    const rows = results.map(
      (r) =>
        `${r.rank},"${r.studentName}","${r.rollNo}",${r.marksObtained},${r.maxMarks},${r.percentage}%,${r.status}`,
    );
    const blob = new Blob([headers.concat(rows.join("\n"))], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${exam?.name || "exam"}_results.csv`;
    a.click();
  };

  if (loading) {
    return (
      <div className="page-shell flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <Spinner className="h-10 w-10 text-indigo-600 border-4" />
          <p className="text-[var(--text-muted)] animate-pulse">Loading exam results...</p>
        </div>
      </div>
    );
  }

  if (error || !exam) {
    return (
      <div className="page-shell">
        <GlassCard className="max-w-xl mx-auto p-8 text-center space-y-4">
          <p className="text-red-500 font-bold">{error || "Exam not found"}</p>
          <Button onClick={() => router.push("/teacher/exams")} variant="secondary">
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to My Exams
          </Button>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="page-shell">
      <div className="max-w-6xl mx-auto space-y-8 animate-fade-in-up">
        <PageHeader
          overline="Exam Analytics & Results"
          title={`${exam.name} — Student Leaderboard`}
          subtitle={`Scoreboard, student rankings, and performance metrics for ${exam.subject || "General"}.`}
          actions={
            <div className="flex gap-3">
              <Link href={`/teacher/exams/${examId}`}>
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="mr-2 h-4 w-4" /> Exam Details
                </Button>
              </Link>
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportCSV}
                disabled={results.length === 0}
                className="flex items-center gap-2"
              >
                <Download size={15} />
                Export CSV
              </Button>
            </div>
          }
        />

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <GlassCard padding="md" className="space-y-1">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-semibold uppercase">Total Attempts</span>
              <Users size={18} className="text-indigo-500" />
            </div>
            <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{stats.total}</p>
          </GlassCard>

          <GlassCard padding="md" className="space-y-1">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-semibold uppercase">Average Score</span>
              <TrendingUp size={18} className="text-emerald-500" />
            </div>
            <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              {stats.avg} <span className="text-xs font-normal text-slate-400">/ {exam.maxMarks}</span>
            </p>
          </GlassCard>

          <GlassCard padding="md" className="space-y-1">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-semibold uppercase">Highest Mark</span>
              <Award size={18} className="text-amber-500" />
            </div>
            <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">
              {stats.highest} <span className="text-xs font-normal text-slate-400">/ {exam.maxMarks}</span>
            </p>
          </GlassCard>

          <GlassCard padding="md" className="space-y-1">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-semibold uppercase">Pass Rate</span>
              <CheckCircle2 size={18} className="text-blue-500" />
            </div>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.passRate}%</p>
          </GlassCard>
        </div>

        {/* Search & Filter Bar */}
        <div className="flex items-center justify-between gap-4">
          <div className="relative max-w-sm w-full">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search student or roll number..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <span className="text-xs font-medium text-slate-400">
            Showing {filteredResults.length} of {results.length} students
          </span>
        </div>

        {/* Results Leaderboard Table */}
        {filteredResults.length === 0 ? (
          <GlassCard padding="lg" className="text-center py-16 space-y-3">
            <Users size={40} className="mx-auto text-slate-300 dark:text-slate-600" />
            <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-300">
              {results.length === 0 ? "No Submissions Yet" : "No Matching Students Found"}
            </h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto">
              {results.length === 0
                ? "Students enrolled in your school will appear on this leaderboard once they submit their exam."
                : "Try adjusting your search query."}
            </p>
          </GlassCard>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 text-xs font-semibold uppercase text-slate-500">
                    <th className="py-3.5 px-4 text-center w-16">Rank</th>
                    <th className="py-3.5 px-4">Student Name</th>
                    <th className="py-3.5 px-4">Roll Number</th>
                    <th className="py-3.5 px-4 text-center">Score</th>
                    <th className="py-3.5 px-4 text-center">Percentage</th>
                    <th className="py-3.5 px-4 text-center">Status</th>
                    <th className="py-3.5 px-4 text-right">Student Record</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-sm">
                  {filteredResults.map((row) => (
                    <tr key={row.studentId || row.rank} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                      <td className="py-3.5 px-4 text-center">
                        <span
                          className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold ${
                            row.rank === 1
                              ? "bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 shadow-sm"
                              : row.rank === 2
                              ? "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200"
                              : row.rank === 3
                              ? "bg-amber-50 text-amber-800 dark:bg-amber-950/30 dark:text-amber-400"
                              : "text-slate-500"
                          }`}
                        >
                          {row.rank}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-semibold text-slate-900 dark:text-slate-100">
                        {row.studentName}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-600 dark:text-slate-300">
                        {row.rollNo || "—"}
                      </td>
                      <td className="py-3.5 px-4 text-center font-bold text-slate-900 dark:text-slate-100">
                        {row.marksObtained} <span className="text-slate-400 font-normal">/ {row.maxMarks}</span>
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <span
                          className={`font-semibold ${
                            row.percentage >= 80
                              ? "text-emerald-600 dark:text-emerald-400"
                              : row.percentage >= 50
                              ? "text-amber-600 dark:text-amber-400"
                              : "text-red-600 dark:text-red-400"
                          }`}
                        >
                          {row.percentage}%
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <Badge
                          variant={
                            row.status === "GRADED"
                              ? "success"
                              : row.status === "SUBMITTED"
                              ? "info"
                              : "warning"
                          }
                        >
                          {row.status}
                        </Badge>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        {row.studentId ? (
                          <Link href={`/students/${row.studentId}`}>
                            <Button variant="ghost" size="sm" className="text-indigo-600 hover:text-indigo-800">
                              View Profile <ChevronRight size={14} className="ml-1" />
                            </Button>
                          </Link>
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
