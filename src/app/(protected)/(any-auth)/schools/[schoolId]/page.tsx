"use client";
import { useEffect } from "react";
import { useParams } from "next/navigation";
import { Spinner } from "@/components/ui/loading";
import { PageHeader } from "@/components/ui/page-header";
import { GlassCard } from "@/components/ui/glass-card";
import { EmptyState } from "@/components/ui/empty-state";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { useSchoolStore } from "@/stores/index";
import { MapPin, Globe, Hash, AlertTriangle } from "lucide-react";

export default function SchoolPage() {
  const { schoolId } = useParams<{ schoolId: string }>();
  const { fetchSchoolById, school, loading, error } = useSchoolStore();

  useEffect(() => {
    if (schoolId) fetchSchoolById(schoolId);
  }, [schoolId, fetchSchoolById]);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Spinner className="h-8 w-8 border-4" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-shell">
        <EmptyState
          icon={AlertTriangle}
          title="Unable to load school"
          description={error}
        />
      </div>
    );
  }

  if (!school) return null;

  const details = [
    { icon: MapPin, label: "City", value: school.city },
    { icon: MapPin, label: "State", value: school.state },
    { icon: Globe, label: "Country", value: school.country },
    { icon: Hash, label: "Pincode", value: school.pincode },
  ];

  return (
    <div className="page-shell animate-fade-in-up">
      <Breadcrumb
        items={[
          { label: "Schools", href: "/schools" },
          { label: school.name },
        ]}
        showHome
        className="mb-6"
      />

      <PageHeader title={school.name} subtitle="School details and information" />

      <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-3xl">
        {details.map((detail, i) => {
          const Icon = detail.icon;
          return (
            <GlassCard
              key={detail.label}
              padding="md"
              className={`animate-fade-in-up stagger-${i + 1}`}
            >
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-[var(--accent-muted)] p-2">
                  <Icon className="h-4 w-4 text-[var(--accent)]" />
                </div>
                <div>
                  <p className="text-xs text-[var(--text-dimmed)] uppercase tracking-wide">
                    {detail.label}
                  </p>
                  <p className="text-sm font-medium text-[var(--text-primary)]">
                    {detail.value || "—"}
                  </p>
                </div>
              </div>
            </GlassCard>
          );
        })}
      </div>
    </div>
  );
}
