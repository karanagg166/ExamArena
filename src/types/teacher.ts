export type Teacher = {
  id: string;
  name: string;
  email: string;
  phoneNo: string;
  experience: number;
  qualifications: string[];
  department: string;
  subjects: string[];
};

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
