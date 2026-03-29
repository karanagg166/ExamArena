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
};
export type UserRole = "STUDENT" | "TEACHER" | "PRINCIPAL" | "SYSTEM_ADMIN";

export type SignUpForm = Omit<User, "id"> & {
  password: string;
  confirmPassword: string;
};
