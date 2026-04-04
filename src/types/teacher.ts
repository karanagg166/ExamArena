// ─── Teacher ────────────────────────────────────────────────────────────────
// Display type — flattened from Prisma Teacher + User relations (used in lists)
export type Teacher = {
  id: string;
  userId: string;
  name: string; // from User relation
  email: string; // from User relation
  phoneNo: string; // from User relation
  experience: number;
  qualifications: string[]; // JSON string in DB, parsed by backend
  department: string;
  subjects: string[]; // JSON string in DB, parsed by backend
  schoolId?: string;
  createdAt?: string;
  updatedAt?: string;
};

// Creating a teacher — only teacher-specific fields (user already exists)
export type TeacherCreate = {
  qualifications: string[];
  experience: number;
  department: string;
  subjects: string[];
};

// Updating a teacher — all optional
export type TeacherUpdate = Partial<TeacherCreate>;

// ─── API Response types ─────────────────────────────────────────────────────
export type TeacherProfileResponse = {
  id: string;
  userId: string;
  qualifications: string[];
  experience: number;
  department: string;
  subjects: string[];
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
