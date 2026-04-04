// ─── Student ────────────────────────────────────────────────────────────────
// Matches Prisma: Student model
export type Student = {
  id: string;
  userId: string;
  rollNo: string;
  parentName: string;
  parentEmail: string;
  dateOfAdmission: string;
  classId: string;
  schoolId: string;
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
  parentName: string;
  parentEmail: string;
  dateOfAdmission: string;
  schoolId: string;
  classId: string;
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
