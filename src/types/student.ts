// ─── Student ────────────────────────────────────────────────────────────────
// Matches Prisma: Student model
export type Student = {
  id: string;
  userId: string;
  rollNo: string;
  parentName?: string | null;
  parentEmail?: string | null;
  fatherName?: string | null;
  fatherEmail?: string | null;
  fatherPhoneNo?: string | null;
  motherName?: string | null;
  motherEmail?: string | null;
  motherPhoneNo?: string | null;
  guardianName?: string | null;
  guardianRelation?: string | null;
  guardianEmail?: string | null;
  guardianPhoneNo?: string | null;
  dateOfAdmission: string;
  classId: string;
  className?: string | null;
  schoolId: string;
  schoolName?: string | null;
  createdAt: string;
  updatedAt: string;
};

// Creating a student — no id/userId/timestamps/dateOfAdmission (server-set)
export type StudentCreate = Omit<
  Student,
  "id" | "userId" | "createdAt" | "updatedAt" | "dateOfAdmission"
>;

// Updating a student — all optional
export type StudentUpdate = Partial<StudentCreate>;

// ─── Display / Response types ───────────────────────────────────────────────
export type StudentProfile = {
  student: Student;
  schoolName: string;
  className: string;
};

export type StudentProfileResponse = {
  id: string;
  userId: string;
  rollNo: string;
  dob: string;
  parentName?: string | null;
  parentEmail?: string | null;
  fatherName?: string | null;
  fatherEmail?: string | null;
  fatherPhoneNo?: string | null;
  motherName?: string | null;
  motherEmail?: string | null;
  motherPhoneNo?: string | null;
  guardianName?: string | null;
  guardianRelation?: string | null;
  guardianEmail?: string | null;
  guardianPhoneNo?: string | null;
  dateOfAdmission: string;
  schoolId: string;
  schoolName?: string | null;
  classId: string;
  className?: string | null;
  user: {
    id: string;
    name: string;
    email: string;
    phoneNo: string;
    city: string;
    state: string;
    country: string;
    pincode: string;
  };
};
