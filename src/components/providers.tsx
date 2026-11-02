"use client";

import { ThemeProvider } from "next-themes";
import { Toaster } from "sonner";
import { AbilityProvider } from "@/lib/casl";
import { BackendAvailabilityProvider } from "@/context/backend-availability-context";
import { BackendStatusBanner } from "@/components/ui/BackendStatusBanner";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem disableTransitionOnChange>
      <AbilityProvider>
        <BackendAvailabilityProvider>
          {children}
          <BackendStatusBanner />
        </BackendAvailabilityProvider>
        <Toaster
          richColors
          closeButton
          position="top-right"
          toastOptions={{
            className: "!border !border-border !bg-card !text-card-foreground !shadow-md",
          }}
        />
      </AbilityProvider>
    </ThemeProvider>
  );
}
