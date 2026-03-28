"use client";

import { ThemeProvider } from "next-themes";
import { Toaster } from "sonner";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      {children}
      <Toaster
        richColors
        closeButton
        theme="dark"
        position="top-right"
        toastOptions={{
          className: "!border !border-zinc-700 !bg-zinc-900 !text-zinc-100",
        }}
      />
    </ThemeProvider>
  );
}
