"use client";

import { ThemeProvider } from "next-themes";
import { Toaster } from "sonner";
import { AbilityProvider } from "@/lib/casl";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem disableTransitionOnChange>
      <AbilityProvider>
        {children}
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
