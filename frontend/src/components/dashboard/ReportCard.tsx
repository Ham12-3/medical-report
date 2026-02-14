"use client";

import type { Report } from "@/lib/api";
import ReportStatusBadge from "@/components/report/ReportStatusBadge";
import ConfidenceIndicator from "@/components/report/ConfidenceIndicator";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface Props {
  report: Report;
}

export default function ReportCard({ report }: Props) {
  const isUploaded = report.status === "uploaded";

  return (
    <div className="group overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm transition-shadow hover:shadow-md">
      {/* Thumbnail */}
      <div className="relative aspect-video bg-gray-100">
        {report.image_url ? (
          <img
            src={`${API_URL}${report.image_url}`}
            alt="Medical scan"
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <svg className="h-12 w-12 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0 0 22.5 18.75V5.25A2.25 2.25 0 0 0 20.25 3H3.75A2.25 2.25 0 0 0 1.5 5.25v13.5A2.25 2.25 0 0 0 3.75 21Z" />
            </svg>
          </div>
        )}
        <div className="absolute left-3 top-3">
          <ReportStatusBadge status={report.status} />
        </div>
      </div>

      {/* Info */}
      <div className="p-4">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-xs text-gray-500">{formatDate(report.created_at)}</span>
          <ConfidenceIndicator score={report.confidence_score} />
        </div>

        {isUploaded ? (
          <Link
            href={`/dashboard/reports/${report.id}?generate=true`}
            className="block w-full rounded-lg bg-medical-600 px-4 py-2 text-center text-sm font-medium text-white transition-colors hover:bg-medical-700"
          >
            Generate Report
          </Link>
        ) : (
          <Link
            href={`/dashboard/reports/${report.id}`}
            className="block w-full rounded-lg border border-medical-200 px-4 py-2 text-center text-sm font-medium text-medical-700 transition-colors hover:bg-medical-50"
          >
            View Report
          </Link>
        )}
      </div>
    </div>
  );
}
