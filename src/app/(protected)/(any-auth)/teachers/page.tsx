"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/axios";
import type { Teacher } from "@/types/teacher";
import TeacherCard from "@/components/teacher/TeacherCard";

type Filters = {
  name: string;
  email: string;
  phoneNo: string;
  department: string;
  subject: string;
  minExperience: string;
  maxExperience: string;
  qualification: string;
};

const INITIAL_FILTERS: Filters = {
  name: "",
  email: "",
  phoneNo: "",
  department: "",
  subject: "",
  minExperience: "",
  maxExperience: "",
  qualification: "",
};

const DEPARTMENTS = [
  "Maths",
  "Science",
  "History",
  "Literature",
  "Art",
  "Music",
  "Physical Education",
];

const QUALIFICATIONS = [
  "BACHELORS",
  "BACHELORS_WITH_HONORS",
  "MASTERS",
  "PHD",
  "OTHER",
];

export default function TeachersPage() {
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<Filters>(INITIAL_FILTERS);
  const [filtersOpen, setFiltersOpen] = useState(true);

  const fetchTeachers = useCallback(async (params: Partial<Filters>) => {
    setLoading(true);
    setError(null);
    try {
      const query = new URLSearchParams(
        Object.fromEntries(Object.entries(params).filter(([, v]) => v !== "")),
      ).toString();

      const { data } = await api.get<Teacher[]>(
        `/api/v1/teachers${query ? `?${query}` : ""}`,
      );
      setTeachers(data);
    } catch (err: unknown) {
      setError((err as Error)?.message ?? "Something went wrong");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timeout = setTimeout(() => {
      fetchTeachers(filters);
    }, 400);
    return () => clearTimeout(timeout);
  }, [filters, fetchTeachers]);

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
      <div className="border-b border-gray-200 bg-white px-6 py-5">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Teachers</h1>
            <p className="mt-0.5 text-sm text-gray-500">
              {loading
                ? "Searching..."
                : `${teachers.length} teacher${teachers.length !== 1 ? "s" : ""} found`}
            </p>
          </div>
          <button
            onClick={() => setFiltersOpen((o) => !o)}
            className="flex items-center gap-2 rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-200"
          >
            <FilterIcon />
            Filters
            {activeFilterCount > 0 && (
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-violet-600 text-xs font-bold text-white">
                {activeFilterCount}
              </span>
            )}
          </button>
        </div>
      </div>

      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-6">
        {filtersOpen && (
          <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              <FilterInput
                label="Name"
                placeholder="e.g. John Doe"
                value={filters.name}
                onChange={(v) => handleFilterChange("name", v)}
              />
              <FilterInput
                label="Email"
                placeholder="e.g. john@school.com"
                value={filters.email}
                onChange={(v) => handleFilterChange("email", v)}
              />
              <FilterInput
                label="Phone"
                placeholder="e.g. 9876543210"
                value={filters.phoneNo}
                onChange={(v) => handleFilterChange("phoneNo", v)}
              />
              <FilterInput
                label="Subject"
                placeholder="e.g. Maths"
                value={filters.subject}
                onChange={(v) => handleFilterChange("subject", v)}
              />

              <FilterSelect
                label="Department"
                value={filters.department}
                options={DEPARTMENTS}
                onChange={(v) => handleFilterChange("department", v)}
              />

              <FilterSelect
                label="Qualification"
                value={filters.qualification}
                options={QUALIFICATIONS}
                onChange={(v) => handleFilterChange("qualification", v)}
              />

              <FilterInput
                label="Min Experience (yrs)"
                placeholder="e.g. 2"
                value={filters.minExperience}
                onChange={(v) => handleFilterChange("minExperience", v)}
                type="number"
              />
              <FilterInput
                label="Max Experience (yrs)"
                placeholder="e.g. 10"
                value={filters.maxExperience}
                onChange={(v) => handleFilterChange("maxExperience", v)}
                type="number"
              />
            </div>

            {activeFilterCount > 0 && (
              <div className="mt-4 flex justify-end border-t border-gray-100 pt-4">
                <button
                  onClick={handleReset}
                  className="text-sm font-medium text-red-500 transition-colors hover:text-red-700"
                >
                  Clear all filters
                </button>
              </div>
            )}
          </div>
        )}

        {loading && (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {!loading && !error && teachers.length === 0 && (
          <div className="py-20 text-center text-gray-400">
            <p className="mb-3 text-4xl">👨‍🏫</p>
            <p className="text-lg font-medium text-gray-600">
              No teachers found
            </p>
            <p className="mt-1 text-sm">Try adjusting your filters</p>
          </div>
        )}

        {!loading && !error && teachers.length > 0 && (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {teachers.map((teacher) => (
              <TeacherCard key={teacher.id} teacher={teacher} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function FilterInput({
  label,
  placeholder,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  placeholder: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-medium uppercase tracking-wide text-gray-500">
        {label}
      </label>
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-10 rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm text-gray-800 placeholder:text-gray-400 transition focus:border-transparent focus:outline-none focus:ring-2 focus:ring-violet-500"
      />
    </div>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-medium uppercase tracking-wide text-gray-500">
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-10 rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm text-gray-800 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-violet-500"
      >
        <option value="">All</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o.replace(/_/g, " ")}
          </option>
        ))}
      </select>
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="animate-pulse space-y-3 rounded-2xl border border-gray-100 bg-white p-5">
      <div className="flex justify-between">
        <div className="h-4 w-2/3 rounded bg-gray-200" />
        <div className="h-4 w-16 rounded bg-gray-200" />
      </div>
      <div className="h-3 w-1/3 rounded bg-gray-100" />
      <div className="space-y-2 pt-1">
        <div className="h-3 w-full rounded bg-gray-100" />
        <div className="h-3 w-3/4 rounded bg-gray-100" />
      </div>
      <div className="flex gap-2 pt-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-5 w-16 rounded-full bg-gray-100" />
        ))}
      </div>
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
