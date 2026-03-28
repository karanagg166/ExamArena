export type Student = {
  id: string;
  rollNo: string;
  parentName: string;
  parentEmail: string;
  dateOfAdmission: string;
  classId: string;
  schoolId: string;
};

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
