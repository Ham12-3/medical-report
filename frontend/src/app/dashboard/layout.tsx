"use client";

import DashboardHeader from "@/components/dashboard/DashboardHeader";
import ErrorBoundary from "@/components/ErrorBoundary";
import ProtectedRoute from "@/components/ProtectedRoute";
import type { ReactNode } from "react";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <DashboardHeader />
        <ErrorBoundary>{children}</ErrorBoundary>
      </div>
    </ProtectedRoute>
  );
}
