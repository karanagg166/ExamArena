"use client";
import { useParams, useRouter } from "next/navigation";
import { ClassStudentsList } from "@/components/school-class/ClassStudentsList";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

export default function PrincipalClassStudentsPage() {
  const router = useRouter();
  const { classId } = useParams<{ classId: string }>();

  return (
    <div className="page-shell text-white animate-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-7xl mx-auto space-y-6">
        <Button
          variant="ghost"
          className="text-zinc-400 hover:text-white pl-0"
          onClick={() => router.back()}
        >
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Class
        </Button>

        <ClassStudentsList classId={classId} />
      </div>
    </div>
  );
}
