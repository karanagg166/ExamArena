export type Principal = {
  id: string;
  teacherId: string;
  schoolId?: string | null;
  experience: number;
  createdAt?: string;
  updatedAt?: string;
};

export type UpdatePrincipalRequest = {
  experience?: number;
};
