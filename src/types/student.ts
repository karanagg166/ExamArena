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