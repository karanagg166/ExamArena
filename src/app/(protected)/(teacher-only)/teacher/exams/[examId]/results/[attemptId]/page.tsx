"use client";

import { useParams } from "next/navigation";
import { TeacherAttemptReview } from "@/components/teacher/grading/TeacherAttemptReview";
import { useAuthStore } from "@/stores/useAuthStore";

export default function TeacherSubmissionPage() {
  const { examId, attemptId } = useParams<{
    examId: string;
    attemptId: string;
  }>();
  const user = useAuthStore((state) => state.user);
  if (!user) return <p role="status">Loading teacher session...</p>;
  if (user.role !== "TEACHER")
    return <p role="alert">Teacher access required.</p>;
  return (
    <TeacherAttemptReview
      key={attemptId}
      examId={examId}
      attemptId={attemptId}
    />
  );
}
