import { Teacher } from "./teacher";

export type SchoolClass = {
  id: string;
  name: string;
  schoolId: string;
  createdAt: string;
  updatedAt: string;
  teachers?: Teacher[];
  schoolName?: string;
};

export type CreateClassRequest = {
  name: string;
  schoolId?: string;
  teachers?: Teacher[];
};

export type UpdateClassRequest = {
  name?: string;
  teachers?: Teacher[];
};
