// @/app/schools/page.tsx
"use client";
import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/axios";
import type { School } from "@/types/school";
import SchoolCard from "@/components/school/SchoolCard";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { EmptyState } from "@/components/ui/empty-state";
import { CardSkeleton } from "@/components/ui/skeleton";
import { SlidersHorizontal, X, School as SchoolIcon } from "lucide-react";

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
      const query = new URLSearchParams(
        Object.fromEntries(Object.entries(params).filter(([, v]) => v !== "")),
      ).toString();

      const { data } = await api.get<School[]>(
        `/api/v1/schools${query ? `?${query}` : ""}`,
      );
      console.log("Fetched schools:", query);
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
  const handleFilterChange = useCallback(
    (key: keyof Filters, value: string) => {
      setFilters((prev) => ({ ...prev, [key]: value }));
    },
    [],
  );

  const handleReset = useCallback(() => {
    setFilters(INITIAL_FILTERS);
  }, []);

  const activeFilterCount = Object.values(filters).filter(Boolean).length;

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="page-shell">
      {/* Page Header */}
      <PageHeader
        title="Schools"
        subtitle={
          loading
            ? "Searching..."
            : `${schools.length} school${schools.length !== 1 ? "s" : ""} found`
        }
        actions={
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setFiltersOpen((o) => !o)}
            className="gap-2"
          >
            <SlidersHorizontal className="h-4 w-4" />
            Filters
            {activeFilterCount > 0 && (
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[var(--accent)] text-[10px] font-bold text-white">
                {activeFilterCount}
              </span>
            )}
          </Button>
        }
      />

      <div className="mt-6 flex flex-col gap-6">
        {/* Filter Panel */}
        {filtersOpen && (
          <div className="glass-panel p-5 animate-fade-in-down">
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
            </div>

            {activeFilterCount > 0 && (
              <div className="mt-4 pt-4 border-t border-[var(--border-subtle)] flex justify-end">
                <button
                  onClick={handleReset}
                  className="inline-flex items-center gap-1.5 text-sm text-[var(--error)] hover:text-[var(--error)]/80 font-medium transition-colors"
                >
                  <X className="h-3.5 w-3.5" />
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
              <CardSkeleton key={i} />
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="panel panel-padding border-[var(--error)]/30 text-sm text-[var(--error)]">
            {error}
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && schools.length === 0 && (
          <EmptyState
            icon={SchoolIcon}
            title="No schools found"
            description="Try adjusting your filters to find what you're looking for."
            action={
              activeFilterCount > 0 ? (
                <Button variant="secondary" size="sm" onClick={handleReset}>
                  Clear filters
                </Button>
              ) : undefined
            }
          />
        )}

        {/* Results Grid */}
        {!loading && !error && schools.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {schools.map((school, i) => (
              <div
                key={school.id}
                className={`animate-fade-in-up stagger-${Math.min(i + 1, 6)}`}
              >
                <SchoolCard
                  school={school}
                  onClick={() => {
                    router.push(`/school/${school.id}`);
                  }}
                />
              </div>
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
      <Label className="text-xs">{label}</Label>
      <Input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
