"use client";
import React from "react";
import { useAuthStore } from "@/stores";

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { loading, initialized, fetchMe } = useAuthStore();
  const [isPublicPage, setIsPublicPage] = React.useState(false);

  React.useEffect(() => {
    const path = window.location.pathname;
    if (path.startsWith('/login') || path.startsWith('/signup') || path === '/') {
      setIsPublicPage(true);
      return;
    }
    fetchMe();
  }, [fetchMe]);

  if ((loading || !initialized) && !isPublicPage) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-muted-foreground text-sm animate-pulse">Loading authorization...</div>
      </div>
    );
  }

  return <>{children}</>;
};
