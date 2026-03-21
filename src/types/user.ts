export type User = {
    id: string;
    name: string;
    email: string;
    phoneNo: string;
    role: UserRole;
    pincode: string;
    city: string;
    state: string;
    country: string;
};
export type UserRole = "student" | "teacher " | "superAdmin" | "systemAdmin";

export type SignUpForm = Omit<User, "id"> & {
    password: string;
    confirmPassword: string;
};