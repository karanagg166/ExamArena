export type SchoolType = "PUBLIC" | "PRIVATE" | "CHARTER" | "INTERNATIONAL";

export type School = {
  id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  country: string;
  pincode: string;
  createdAt: string;
  updatedAt: string;
  schoolCode: string;
  type: SchoolType;
  email?: string;
  website?: string;
  phone?: string;
  principalName?: string;
};
