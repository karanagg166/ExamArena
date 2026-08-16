export type JoinRequestStatus = "PENDING" | "APPROVED" | "REJECTED";

export type ClassJoinRequest = {
  id: string;
  studentUserId: string;
  classId: string;
  className: string;
  schoolId?: string | null;
  status: JoinRequestStatus;
  requestedAt: string;
  decidedAt?: string | null;
  studentName: string;
  studentEmail: string;
};

export type JoinRequestDecisionPayload = {
  status: "APPROVED" | "REJECTED";
  rollNo?: string;
  autoRollNo?: boolean;
};

export type TeacherClassJoinRequest = {
  id: string;
  teacherId: string;
  teacherName: string;
  teacherEmail: string;
  classId: string;
  className: string;
  schoolId: string;
  subject?: string | null;
  status: JoinRequestStatus;
  requestedAt: string;
  decidedAt?: string | null;
  decidedBy?: string | null;
};

export type TeacherSchoolJoinRequest = {
  id: string;
  teacherId: string;
  teacherName: string;
  teacherEmail: string;
  teacherDepartment?: string | null;
  schoolId: string;
  schoolName: string;
  status: JoinRequestStatus;
  requestedAt: string;
  decidedAt?: string | null;
  decidedBy?: string | null;
};

export type TeacherAssignClassesPayload = {
  teacherId: string;
  classIds: string[];
  subject?: string | null;
};

