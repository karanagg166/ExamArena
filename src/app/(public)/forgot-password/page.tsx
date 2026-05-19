import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function ForgotPasswordPage() {
  return (
    <div className="flex h-screen w-full items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6 rounded-lg border bg-card p-8 shadow-sm">
        <div className="space-y-2 text-center">
          <h1 className="text-2xl font-bold tracking-tight">Forgot Password</h1>
          <p className="text-muted-foreground">
            This feature is currently under development.
          </p>
        </div>
        <div className="space-y-4 pt-4">
          <Button asChild className="w-full">
            <Link href="/login">Return to Login</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
