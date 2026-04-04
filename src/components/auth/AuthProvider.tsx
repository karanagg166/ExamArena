"use client";
import React from "react";
import { useAuthStore } from "@/stores";

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { loading, fetchMe } = useAuthStore();
  const [isPublicPage, setIsPublicPage] = React.useState(false);

  React.useEffect(() => {
    const path = window.location.pathname;
    if (path.startsWith('/login') || path.startsWith('/signup') || path === '/') {
      setIsPublicPage(true);
      return;
    }
    fetchMe();
  }, [fetchMe]);

  if (loading && !isPublicPage) {
    return <div>Loading...</div>;
  }

  return <>{children}</>;
};
