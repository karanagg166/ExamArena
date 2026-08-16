"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function NewClassPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/teacher/classes");
  }, [router]);

  return null;
}
