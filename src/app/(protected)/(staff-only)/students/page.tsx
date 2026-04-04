"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/axios";
import StudentCard, { StudentListItem } from "@/components/student/StudentCard";

type Filters = {
  name: string;
  email: string;
  rollNo: string;
  classYear: string;
  section: string;
  schoolName: string;
  schoolCode: string;
};

const INITIAL_FILTERS: Filters = {
  name: "",
  email: "",
  rollNo: "",
  classYear: "",
  section: "",
  schoolName: "",
  schoolCode: "",
};

export default function StudentsPage() {
  const [students, setStudents] = useState<StudentListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<Filters>(INITIAL_FILTERS);
  const [filtersOpen, setFiltersOpen] = useState(true);

  const fetchStudents = useCallback(async (params: Partial<Filters>) => {
    setLoading(true);
    setError(null);
    try {
      const query = new URLSearchParams(
        Object.fromEntries(Object.entries(params).filter(([, v]) => v !== "")),
      ).toString();

      const { data } = await api.get<StudentListItem[]>(
        `/api/v1/students${query ? `?${query}` : ""}`,
      );
      setStudents(data);
    } catch (err: unknown) {
      const axiosMsg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail;
      setError(axiosMsg ?? (err as Error)?.message ?? "Something went wrong");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timeout = setTimeout(() => {
      fetchStudents(filters);
    }, 400);
    return () => clearTimeout(timeout);
  }, [filters, fetchStudents]);

  const handleFilterChange = useCallback(
    (key: keyof Filters, value: string) => {
      setFilters((prev) => ({ ...prev, [key]: value }));
    },
    [],
  );

  const handleReset = useCallback(() => setFilters(INITIAL_FILTERS), []);
  const activeFilterCount = Object.values(filters).filter(Boolean).length;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-5">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Students</h1>
            <p className="mt-0.5 text-sm text-gray-500">
              {loading
                ? "Searching…"
                : `${students.length} student${students.length !== 1 ? "s" : ""} found`}
            </p>
          </div>
          <button
            id="students-filter-toggle"
            onClick={() => setFiltersOpen((o) => !o)}
            className="flex items-center gap-2 rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-200"
          >
            <FilterIcon />
            Filters
            {activeFilterCount > 0 && (
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white">
                {activeFilterCount}
              </span>
            )}
          </button>
        </div>
      </div>

      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-6">
        {/* Filter panel */}
        {filtersOpen && (
          <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              <FilterInput
                id="filter-name"
                label="Name"
                placeholder="e.g. Rahul Sharma"
                value={filters.name}
                onChange={(v) => handleFilterChange("name", v)}
              />
              <FilterInput
                id="filter-email"
                label="Email"
                placeholder="e.g. rahul@school.com"
                value={filters.email}
                onChange={(v) => handleFilterChange("email", v)}
              />
              <FilterInput
                id="filter-rollno"
                label="Roll Number"
                placeholder="e.g. 42"
                value={filters.rollNo}
                onChange={(v) => handleFilterChange("rollNo", v)}
              />
              <FilterInput
                id="filter-classyear"
                label="Class Year"
                placeholder="e.g. 10th"
                value={filters.classYear}
                onChange={(v) => handleFilterChange("classYear", v)}
              />
              <FilterInput
                id="filter-section"
                label="Section"
                placeholder="e.g. A"
                value={filters.section}
                onChange={(v) => handleFilterChange("section", v)}
              />
              <FilterInput
                id="filter-schoolname"
                label="School Name"
                placeholder="e.g. Sunrise Public School"
                value={filters.schoolName}
                onChange={(v) => handleFilterChange("schoolName", v)}
              />
              <FilterInput
                id="filter-schoolcode"
                label="School Code"
                placeholder="e.g. SPS-2026"
                value={filters.schoolCode}
                onChange={(v) => handleFilterChange("schoolCode", v)}
              />
            </div>

            {activeFilterCount > 0 && (
              <div className="mt-4 flex justify-end border-t border-gray-100 pt-4">
                <button
                  id="students-filter-reset"
                  onClick={handleReset}
                  className="text-sm font-medium text-red-500 transition-colors hover:text-red-700"
                >
                  Clear all filters
                </button>
              </div>
            )}
          </div>
        )}

        {/* Loading skeletons */}
        {loading && (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && students.length === 0 && (
          <div className="py-20 text-center text-gray-400">
            <p className="mb-3 text-4xl">🎓</p>
            <p className="text-lg font-medium text-gray-600">
              No students found
            </p>
            <p className="mt-1 text-sm">Try adjusting your filters</p>
          </div>
        )}

        {/* Student cards */}
        {!loading && !error && students.length > 0 && (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {students.map((student) => (
              <StudentCard key={student.id} student={student} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Sub-components ────────────────────────────────────────────────────── */

function FilterInput({
  id,
  label,
  placeholder,
  value,
  onChange,
  type = "text",
}: {
  id: string;
  label: string;
  placeholder: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={id}
        className="text-xs font-medium uppercase tracking-wide text-gray-500"
      >
        {label}
      </label>
      <input
        id={id}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-10 rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm text-gray-800 placeholder:text-gray-400 transition focus:border-transparent focus:outline-none focus:ring-2 focus:ring-indigo-500"
      />
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="animate-pulse space-y-3 rounded-2xl border border-gray-100 bg-white p-5">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-full bg-gray-200" />
        <div className="flex-1 space-y-1.5">
          <div className="h-4 w-2/3 rounded bg-gray-200" />
          <div className="h-3 w-1/2 rounded bg-gray-100" />
        </div>
        <div className="h-6 w-16 rounded-full bg-gray-200" />
      </div>
      <div className="h-3 w-1/3 rounded bg-gray-100" />
    </div>
  );
}

function FilterIcon() {
  return (
    <svg
      width="15"
      height="15"
      viewBox="0 0 15 15"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M1 3h13M3 7h9M5 11h5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}
