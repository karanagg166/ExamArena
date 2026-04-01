// ─── Enums (match Prisma Role) ──────────────────────────────────────────────
export type UserRole = "STUDENT" | "TEACHER" | "ADMIN" | "PRINCIPAL";

// ─── User ───────────────────────────────────────────────────────────────────
// Matches Prisma: User model
export type User = {
  id: string;
  name: string;
  email: string;
  phoneNo: string;
  dateOfBirth: string;
  role: UserRole;
  pincode: string;
  city: string;
  state: string;
  country: string;
  createdAt: string;
  updatedAt: string;
};

// Signup form — no id/timestamps (server-generated)
export type SignUpForm = Omit<User, "id" | "createdAt" | "updatedAt"> & {
  password: string;
  confirmPassword: string;
};
