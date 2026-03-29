"use client";

import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { NewClass } from "@/components/school-class/NewClass";
import { Button } from "@/components/ui/button";

export default function NewClassPage() {
  const router = useRouter();

  return (
    <div className="page-shell text-white">
      <div className="mb-4">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
      </div>

      <NewClass onClose={() => router.push("/principal/school/classes")} />
    </div>
  );
}
