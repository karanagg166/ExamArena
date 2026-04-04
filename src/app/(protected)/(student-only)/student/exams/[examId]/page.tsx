import { redirect } from "next/navigation";

export default function StudentExamShell({ params }: { params: { examId: string } }) {
  redirect(`/student/exams/${params.examId}/start`);
}
