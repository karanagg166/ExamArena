"use client";
import React from "react";
import { useAuthStore } from "@/stores";

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
    children,
}) => {
    const { loading, fetchMe } = useAuthStore();

    React.useEffect(() => {
        fetchMe();
    }, [fetchMe]);
    if (loading) {
        return <div>Loading...</div>;
    }

    return <>{children}</>;
};