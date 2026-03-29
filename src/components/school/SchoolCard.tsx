"use client";
import { useRouter } from "next/navigation";
import type { School } from "@/types/school";

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
    <div
      onClick={handleClick}
      className={`
        group relative bg-white border border-gray-100 rounded-2xl p-5
        shadow-sm hover:shadow-md hover:-translate-y-0.5
        transition-all duration-200 cursor-pointer overflow-hidden
      `}
    >
      {/* Accent bar */}
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-violet-500 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />

      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-semibold text-gray-900 truncate leading-snug">
            {school.name}
          </h3>
          <p className="text-xs text-indigo-600 font-mono mt-0.5">
            {school.schoolCode}
          </p>
        </div>
        <span className="shrink-0 text-xs bg-indigo-50 text-indigo-700 font-medium px-2.5 py-1 rounded-full border border-indigo-100">
          {school.type
            ? school.type.charAt(0) + school.type.slice(1).toLowerCase()
            : "Public"}
        </span>
      </div>

      {/* Details grid */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-2.5 text-sm">
        <Detail icon="🏙️" label="City" value={school.city} />
        <Detail icon="🗺️" label="State" value={school.state} />
        <Detail icon="🌍" label="Country" value={school.country} />
        <Detail icon="📮" label="Pincode" value={school.pincode} />
        <Detail icon="👤" label="Principal" value={school.principalName} />
        <Detail icon="📞" label="Phone" value={school.phone} />
      </div>

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between">
        <span className="text-xs text-gray-400">
          Est. {new Date(school.createdAt).getFullYear()}
        </span>
        <span className="text-xs text-gray-400 truncate max-w-[55%] text-right">
          {school.email}
        </span>
      </div>
    </div>
  );
}

function Detail({
  icon,
  label,
  value,
}: {
  icon: string;
  label: string;
  value?: string;
}) {
  return (
    <div className="flex items-start gap-1.5 min-w-0">
      <span className="text-sm shrink-0 mt-0.5">{icon}</span>
      <div className="min-w-0">
        <p className="text-[10px] text-gray-400 uppercase tracking-wide leading-none mb-0.5">
          {label}
        </p>
        <p className="text-gray-700 font-medium truncate text-xs">
          {value || "—"}
        </p>
      </div>
    </div>
  );
}
