// @/app/schools/page.tsx
'use client';
import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/axios";
import type { School } from "@/types/school";
import SchoolCard from "@/components/school/SchoolCard";
import { useRouter } from "next/navigation";
// ─── Filter State ─────────────────────────────────────────────────────────────

type Filters = {
  name: string;
  city: string;
  state: string;
  country: string;
  pincode: string;
  schoolCode: string;
  principalName: string;
  phone: string;
  email: string;
};

const INITIAL_FILTERS: Filters = {
  name: "",
  city: "",
  state: "",
  country: "",
  pincode: "",
  schoolCode: "",
  principalName: "",
  phone: "",
  email: "",
};

// ─── Component ────────────────────────────────────────────────────────────────

export default function SchoolsPage() {
  const router = useRouter();
  const [schools, setSchools] = useState<School[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<Filters>(INITIAL_FILTERS);
  const [filtersOpen, setFiltersOpen] = useState(true);

  // ── Fetch with filters ─────────────────────────────────────────────────────
  const fetchSchools = useCallback(async (params: Partial<Filters>) => {
    setLoading(true);
    setError(null);
    try {
      // Only send filters that have a value
      const query = new URLSearchParams(
        Object.fromEntries(
          Object.entries(params).filter(([_, v]) => v !== "")
        )
      ).toString();

      const { data } = await api.get<School[]>(
        `/api/v1/schools${query ? `?${query}` : ""}`
      );
      console.log("Fetched schools:", query); // Debug log
      setSchools(data);
    } catch (err: unknown) {
      console.log("Failed to fetch schools:", err);
      setError((err as Error)?.message ?? "Something went wrong");
    } finally {
      setLoading(false);
    }
  }, []);

  // ── Debounce: wait 400ms after user stops typing ───────────────────────────
  useEffect(() => {
    const timeout = setTimeout(() => {
      fetchSchools(filters);
    }, 400);

    return () => clearTimeout(timeout);
  }, [filters, fetchSchools]);

  // ── Handlers ───────────────────────────────────────────────────────────────
  const handleFilterChange = useCallback((key: keyof Filters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }, []);

  const handleReset = useCallback(() => {
    setFilters(INITIAL_FILTERS);
  }, []);

  const activeFilterCount = Object.values(filters).filter(Boolean).length;

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-50">

      {/* Page Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Schools</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {loading
                ? "Searching..."
                : `${schools.length} school${schools.length !== 1 ? "s" : ""} found`}
            </p>
          </div>
          <button
            onClick={() => setFiltersOpen((o) => !o)}
            className="flex items-center gap-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 px-4 py-2 rounded-lg transition-colors"
          >
            <FilterIcon />
            Filters
            {activeFilterCount > 0 && (
              <span className="bg-indigo-600 text-white text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center">
                {activeFilterCount}
              </span>
            )}
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 flex flex-col gap-6">

        {/* Filter Panel */}
        {filtersOpen && (
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              <FilterInput
                label="School Name"
                placeholder="e.g. Sunrise Academy"
                value={filters.name}
                onChange={(v) => handleFilterChange("name", v)}
              />
              <FilterInput
                label="School Code"
                placeholder="e.g. SCH001"
                value={filters.schoolCode}
                onChange={(v) => handleFilterChange("schoolCode", v)}
              />
              <FilterInput
                label="Principal Name"
                placeholder="e.g. John Doe"
                value={filters.principalName}
                onChange={(v) => handleFilterChange("principalName", v)}
              />
              <FilterInput
                label="City"
                placeholder="e.g. Mumbai"
                value={filters.city}
                onChange={(v) => handleFilterChange("city", v)}
              />
              <FilterInput
                label="State"
                placeholder="e.g. Maharashtra"
                value={filters.state}
                onChange={(v) => handleFilterChange("state", v)}
              />
              <FilterInput
                label="Country"
                placeholder="e.g. India"
                value={filters.country}
                onChange={(v) => handleFilterChange("country", v)}
              />
              <FilterInput
                label="Pincode"
                placeholder="e.g. 400001"
                value={filters.pincode}
                onChange={(v) => handleFilterChange("pincode", v)}
              />
              <FilterInput
                label="Phone"
                placeholder="e.g. 9876543210"
                value={filters.phone}
                onChange={(v) => handleFilterChange("phone", v)}
              />
              <FilterInput
                label="Email"
                placeholder="e.g. info@school.com"
                value={filters.email}
                onChange={(v) => handleFilterChange("email", v)}
              />
              {/* 
                ── Add SchoolType dropdown here later ──
                <FilterSelect ... /> 
              */}
            </div>

            {activeFilterCount > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-100 flex justify-end">
                <button
                  onClick={handleReset}
                  className="text-sm text-red-500 hover:text-red-700 font-medium transition-colors"
                >
                  Clear all filters
                </button>
              </div>
            )}
          </div>
        )}

        {/* Loading Skeletons */}
        {loading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {Array.from({ length: 6 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-5 py-4 text-sm">
            {error}
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && schools.length === 0 && (
          <div className="text-center py-20 text-gray-400">
            <p className="text-4xl mb-3">🏫</p>
            <p className="text-lg font-medium text-gray-600">No schools found</p>
            <p className="text-sm mt-1">Try adjusting your filters</p>
          </div>
        )}

        {/* Results Grid */}
        {!loading && !error && schools.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {schools.map((school) => (
              <SchoolCard key={school.id} school={school} onClick={() => { router.push(`/school/${school.id}`) }} />
            ))}
          </div>
        )}

      </div>
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function FilterInput({
  label,
  placeholder,
  value,
  onChange,
}: {
  label: string;
  placeholder: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
        {label}
      </label>
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-10 rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
      />
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="bg-white border border-gray-100 rounded-2xl p-5 space-y-3 animate-pulse">
      <div className="flex justify-between">
        <div className="h-4 bg-gray-200 rounded w-2/3" />
        <div className="h-4 bg-gray-200 rounded w-16" />
      </div>
      <div className="h-3 bg-gray-100 rounded w-1/3" />
      <div className="grid grid-cols-2 gap-2 pt-1">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-8 bg-gray-100 rounded" />
        ))}
      </div>
      <div className="h-px bg-gray-100 mt-2" />
      <div className="flex justify-between pt-1">
        <div className="h-3 bg-gray-100 rounded w-16" />
        <div className="h-3 bg-gray-100 rounded w-24" />
      </div>
    </div>
  );
}

function FilterIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M1 3h13M3 7h9M5 11h5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}