// ─── Enums (match Prisma SchoolType) ────────────────────────────────────────
export type SchoolType = "PUBLIC" | "PRIVATE" | "CHARTER" | "INTERNATIONAL";

// ─── School ─────────────────────────────────────────────────────────────────
// Matches Prisma: School model
export type School = {
  id: string;
  name: string;
  createdBy: string; // userId of creator — exists in Prisma
  address: string;
  city: string;
  state: string;
  country: string;
  pincode: string;
  schoolCode: string;
  type: SchoolType;
  email?: string;
  website?: string;
  phoneNo?: string; // Prisma: phoneNo String?
  createdAt: string;
  updatedAt: string;
  // Frontend-computed fields (from relations, not in Prisma model directly)
  principalName?: string;
};

// Creating a school — no id/timestamps/createdBy (server-injected)
export type SchoolCreate = Omit<
  School,
  "id" | "createdAt" | "updatedAt" | "createdBy" | "principalName"
>;

// Updating a school — all optional
export type SchoolUpdate = Partial<SchoolCreate>;
