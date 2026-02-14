"use client";

import type { Finding } from "@/lib/types";

interface Props {
  findings: Finding[];
}

const SEVERITY_COLORS: Record<string, { bg: string; text: string }> = {
  critical: { bg: "bg-red-100", text: "text-red-800" },
  high: { bg: "bg-orange-100", text: "text-orange-800" },
  moderate: { bg: "bg-yellow-100", text: "text-yellow-800" },
  low: { bg: "bg-blue-100", text: "text-blue-800" },
  normal: { bg: "bg-green-100", text: "text-green-800" },
};

function getSeverityStyle(severity: string) {
  return SEVERITY_COLORS[severity] || { bg: "bg-gray-100", text: "text-gray-800" };
}

export default function FindingsSection({ findings }: Props) {
  if (findings.length === 0) return null;

  return (
    <div>
      <h3 className="mb-4 text-lg font-semibold text-gray-900">Findings</h3>
      <div className="space-y-4">
        {findings.map((finding, i) => {
          const style = getSeverityStyle(finding.severity);
          const confPct = Math.round(finding.confidence * 100);
          return (
            <div
              key={finding.id || i}
              className="rounded-lg border border-gray-200 bg-white p-4"
            >
              <div className="mb-2 flex items-center justify-between">
                <h4 className="font-medium text-gray-900">{finding.finding}</h4>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${style.bg} ${style.text}`}
                >
                  {finding.severity}
                </span>
              </div>
              <p className="mb-3 text-sm text-gray-500">{finding.location}</p>
              <p className="mb-3 text-sm text-gray-700">{finding.details}</p>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">Confidence</span>
                <div className="h-1.5 w-24 overflow-hidden rounded-full bg-gray-200">
                  <div
                    className={`h-full rounded-full ${confPct >= 80 ? "bg-green-500" : confPct >= 50 ? "bg-yellow-500" : "bg-red-500"}`}
                    style={{ width: `${confPct}%` }}
                  />
                </div>
                <span className="text-xs font-medium text-gray-600">{confPct}%</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
