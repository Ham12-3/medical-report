"use client";

import type { Report } from "@/lib/api";

const STATUS_STYLES: Record<string, { dot: string; label: string }> = {
  uploaded:   { dot: "bg-yellow-400", label: "Uploaded" },
  processing: { dot: "bg-blue-400",   label: "Processing" },
  completed:  { dot: "bg-green-500",  label: "Completed" },
  failed:     { dot: "bg-red-500",    label: "Failed" },
  pending:    { dot: "bg-gray-400",   label: "Pending" },
};

function getStatus(status: string) {
  return STATUS_STYLES[status] || { dot: "bg-gray-400", label: status };
}

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
  reports: Report[];
  loading: boolean;
}

export default function ReportList({ reports, loading }: Props) {
  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-6 w-6 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  if (reports.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white px-6 py-12 text-center">
        <p className="text-sm text-gray-500">
          No reports yet. Upload a medical image to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-gray-200 bg-gray-50">
          <tr>
            <th className="px-4 py-3 font-medium text-gray-600">Image</th>
            <th className="px-4 py-3 font-medium text-gray-600">Status</th>
            <th className="px-4 py-3 font-medium text-gray-600">Confidence</th>
            <th className="px-4 py-3 font-medium text-gray-600">Created</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {reports.map((report) => {
            const s = getStatus(report.status);
            return (
              <tr key={report.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  {report.image_url ? (
                    <div className="h-10 w-10 overflow-hidden rounded bg-gray-100">
                      <img
                        src={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${report.image_url}`}
                        alt="Medical scan"
                        className="h-full w-full object-cover"
                      />
                    </div>
                  ) : (
                    <div className="flex h-10 w-10 items-center justify-center rounded bg-gray-100">
                      <span className="text-xs text-gray-400">N/A</span>
                    </div>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className="inline-flex items-center gap-1.5">
                    <span className={`inline-block h-2 w-2 rounded-full ${s.dot}`} />
                    {s.label}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {report.confidence_score != null
                    ? `${(report.confidence_score * 100).toFixed(0)}%`
                    : "-"}
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {formatDate(report.created_at)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
