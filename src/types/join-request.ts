export type JoinRequestStatus = "PENDING" | "APPROVED" | "REJECTED";

export type ClassJoinRequest = {
  id: string;
  studentUserId: string;
  classId: string;
  className: string;
  status: JoinRequestStatus;
  requestedAt: string;
  decidedAt?: string | null;
  studentName: string;
  studentEmail: string;
};
