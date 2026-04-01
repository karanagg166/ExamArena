import type { Teacher } from "./teacher";

// ─── SchoolClass ────────────────────────────────────────────────────────────
// Matches Prisma: SchoolClass model
export type SchoolClass = {
  id: string;
  name: string; // display name, e.g. "12th - A"
  year: string; // grade/year level, e.g. "12th", "10th"
  section: string; // batch/section, e.g. "A", "B", "C"
  schoolId: string;
  teacherId?: string; // class teacher / homeroom teacher
  createdAt: string;
  updatedAt: string;
  // Frontend-computed fields (from relations)
  teachers?: Teacher[];
  schoolName?: string;
};

// Creating a class — no id/timestamps (server-generated)
export type CreateClassRequest = {
  name: string; // or auto-generate from year+section
  year: string;
  section?: string; // defaults to "A" in Prisma
  schoolId?: string;
};

// Updating a class
export type UpdateClassRequest = {
  id: string;
  name?: string;
  year?: string;
  section?: string;
  teacherId?: string; // assign/change class teacher
};
