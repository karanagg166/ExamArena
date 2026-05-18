// This route group page redirects to the root landing page.
// The primary landing page is at /src/app/page.tsx
import { redirect } from "next/navigation";

export default function PublicGroupPage() {
  redirect("/");
}
