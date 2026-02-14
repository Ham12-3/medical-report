"use client";

import { useAuth } from "@/context/AuthContext";

export default function DashboardHeader() {
  const { user, logout } = useAuth();

  return (
    <header className="border-b border-medical-200 bg-white shadow-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
        <div className="flex items-center gap-3">
          {/* Medical cross icon */}
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-medical-600">
            <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
          </div>
          <h1 className="text-lg font-semibold text-medical-950">MedAI Reports</h1>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">{user?.email}</span>
          <button
            onClick={logout}
            className="rounded-md px-3 py-1.5 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900"
          >
            Sign out
          </button>
        </div>
      </div>
    </header>
  );
}
