"use client";

import type { Report } from "@/lib/api";
import ReportCard from "./ReportCard";

interface Props {
  reports: Report[];
  loading: boolean;
}

function SkeletonCard() {
  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="aspect-video animate-pulse bg-gray-200" />
      <div className="space-y-3 p-4">
        <div className="flex items-center justify-between">
          <div className="h-3 w-24 animate-pulse rounded bg-gray-200" />
          <div className="h-3 w-16 animate-pulse rounded bg-gray-200" />
        </div>
        <div className="h-9 w-full animate-pulse rounded-lg bg-gray-200" />
      </div>
    </div>
  );
}

export default function ReportCardGrid({ reports, loading }: Props) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (reports.length === 0) {
    return (
      <div className="rounded-xl border-2 border-dashed border-gray-300 bg-white px-6 py-16 text-center">
        <svg className="mx-auto mb-4 h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
        </svg>
        <p className="text-sm font-medium text-gray-900">No reports yet</p>
        <p className="mt-1 text-sm text-gray-500">
          Upload a medical image above to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {reports.map((report) => (
        <ReportCard key={report.id} report={report} />
      ))}
    </div>
  );
}
