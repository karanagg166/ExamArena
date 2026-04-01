// ─── Principal ──────────────────────────────────────────────────────────────
// Matches Prisma: Principal model
export type Principal = {
  id: string;
  teacherId: string;
  schoolId?: string | null;
  experience: number;
  createdAt: string;
  updatedAt: string;
};

// Creating a principal — no id/timestamps (server-generated)
export type PrincipalCreate = {
  schoolId?: string;
  experience: number;
};

// Updating a principal — all optional
export type UpdatePrincipalRequest = {
  id: string;
  experience?: number;
  schoolId?: string;
};
