"use client";
import { useRouter } from "next/navigation";
import type { School } from "@/types/school";
import {
  MapPin,
  Globe,
  Hash,
  User,
  Phone,
  Mail,
} from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";

interface SchoolCardProps {
  school: School;
  onClick?: (school: School) => void;
}

export default function SchoolCard({ school, onClick }: SchoolCardProps) {
  const router = useRouter();

  const handleClick = () => {
    onClick?.(school);
    router.push(`/schools/${school.id}`);
  };

  return (
    <GlassCard
      interactive
      padding="md"
      className="cursor-pointer group"
      onClick={handleClick}
    >
      {/* Accent bar on hover */}
      <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-[var(--accent)] to-violet-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-t-2xl" />

      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-semibold text-[var(--text-primary)] truncate leading-snug">
            {school.name}
          </h3>
          <p className="text-xs text-[var(--accent)] font-mono mt-0.5">
            {school.schoolCode}
          </p>
        </div>
        <span className="shrink-0 text-xs font-medium px-2.5 py-1 rounded-full bg-[var(--accent-muted)] text-[var(--accent)] border border-[var(--accent)]/20">
          {school.type
            ? school.type.charAt(0) + school.type.slice(1).toLowerCase()
            : "Public"}
        </span>
      </div>

      {/* Details grid */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-2.5 text-sm">
        <Detail icon={MapPin} label="City" value={school.city} />
        <Detail icon={MapPin} label="State" value={school.state} />
        <Detail icon={Globe} label="Country" value={school.country} />
        <Detail icon={Hash} label="Pincode" value={school.pincode} />
        <Detail icon={User} label="Principal" value={school.principalName} />
        <Detail icon={Phone} label="Phone" value={school.phoneNo} />
      </div>

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between">
        <span className="text-xs text-[var(--text-dimmed)]">
          Est. {new Date(school.createdAt).getFullYear()}
        </span>
        <span className="text-xs text-[var(--text-dimmed)] truncate max-w-[55%] text-right flex items-center gap-1">
          <Mail className="h-3 w-3" />
          {school.email}
        </span>
      </div>
    </GlassCard>
  );
}

function Detail({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value?: string;
}) {
  return (
    <div className="flex items-start gap-1.5 min-w-0">
      <Icon className="h-3.5 w-3.5 text-[var(--text-dimmed)] mt-0.5 shrink-0" />
      <div className="min-w-0">
        <p className="text-[10px] text-[var(--text-dimmed)] uppercase tracking-wide leading-none mb-0.5">
          {label}
        </p>
        <p className="text-[var(--text-secondary)] font-medium truncate text-xs">
          {value || "—"}
        </p>
      </div>
    </div>
  );
}
