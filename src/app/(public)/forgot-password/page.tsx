import Link from "next/link";
import { Button } from "@/components/ui/button";
import { AlertCircle, ArrowLeft, Mail } from "lucide-react";

export default function ForgotPasswordPage() {
  return (
    <div className="flex min-h-screen w-full items-center justify-center p-4 bg-background">
      <div className="w-full max-w-md space-y-6 rounded-2xl border border-border bg-card p-8 shadow-xl">
        <div className="flex flex-col items-center space-y-3 text-center">
          <div className="rounded-full bg-amber-500/10 p-3 text-amber-400">
            <Mail className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Password Reset
          </h1>
          <p className="text-sm text-muted-foreground">
            Self-service email password recovery is currently unavailable because an outbound transactional email service (SMTP/SES) has not been provisioned.
          </p>
        </div>

        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-xs text-amber-300 space-y-2">
          <div className="flex items-center gap-2 font-semibold text-amber-200">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>Administrator Assistance Required</span>
          </div>
          <p className="leading-relaxed">
            Please contact your school Principal or organization Administrator to have your account password reset securely from the administrative portal.
          </p>
        </div>

        <div className="space-y-4 pt-2">
          <Button asChild className="w-full bg-indigo-600 hover:bg-indigo-700 text-white">
            <Link href="/login" className="flex items-center justify-center gap-2">
              <ArrowLeft className="h-4 w-4" />
              <span>Return to Login</span>
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
