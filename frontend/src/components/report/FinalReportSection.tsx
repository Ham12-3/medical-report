"use client";

import type { FinalReport } from "@/lib/types";

interface Props {
  report: FinalReport;
}

const RISK_COLORS: Record<string, string> = {
  critical: "border-red-500 bg-red-50 text-red-800",
  high: "border-orange-500 bg-orange-50 text-orange-800",
  moderate: "border-yellow-500 bg-yellow-50 text-yellow-800",
  low: "border-green-500 bg-green-50 text-green-800",
};

export default function FinalReportSection({ report }: Props) {
  return (
    <div className="space-y-8">
      <h3 className="text-lg font-semibold text-gray-900">Report</h3>

      {/* Executive Summary */}
      <div className="rounded-lg border-l-4 border-medical-500 bg-medical-50 p-5">
        <h4 className="mb-2 text-sm font-semibold uppercase tracking-wide text-medical-800">
          Executive Summary
        </h4>
        <p className="text-sm leading-relaxed text-medical-900">
          {report.executive_summary}
        </p>
      </div>

      {/* Detailed Findings */}
      {report.detailed_findings && report.detailed_findings.length > 0 && (
        <div>
          <h4 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-700">
            Detailed Findings
          </h4>
          <div className="space-y-4">
            {report.detailed_findings.map((f, i) => (
              <div
                key={i}
                className="border-l-4 border-medical-300 bg-white p-4 pl-5 rounded-r-lg"
              >
                <h5 className="mb-2 font-medium text-gray-900">{f.finding}</h5>
                <div className="space-y-2 text-sm text-gray-700">
                  <p>{f.analysis}</p>
                  {f.supporting_evidence && (
                    <p className="text-gray-500">
                      <span className="font-medium text-gray-600">Evidence: </span>
                      {f.supporting_evidence}
                    </p>
                  )}
                  {f.clinical_significance && (
                    <p className="text-gray-500">
                      <span className="font-medium text-gray-600">
                        Clinical Significance:{" "}
                      </span>
                      {f.clinical_significance}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Assessment */}
      {report.risk_assessment && report.risk_assessment.length > 0 && (
        <div>
          <h4 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-700">
            Risk Assessment
          </h4>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {report.risk_assessment.map((risk, i) => (
              <div
                key={i}
                className={`rounded-lg border-l-4 p-4 ${RISK_COLORS[risk.level] || "border-gray-300 bg-gray-50 text-gray-800"}`}
              >
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-sm font-medium">{risk.category}</span>
                  <span className="rounded-full bg-white/50 px-2 py-0.5 text-xs font-medium uppercase">
                    {risk.level}
                  </span>
                </div>
                <p className="text-xs">{risk.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Next Steps */}
      {report.next_steps && report.next_steps.length > 0 && (
        <div>
          <h4 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-700">
            Recommended Next Steps
          </h4>
          <ul className="space-y-2">
            {report.next_steps.map((step, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-medical-100 text-xs font-medium text-medical-700">
                  {i + 1}
                </span>
                {step}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Methodology */}
      {report.methodology && (
        <div className="rounded-lg bg-gray-50 p-4">
          <h4 className="mb-2 text-sm font-semibold text-gray-600">Methodology</h4>
          <p className="text-sm text-gray-600">{report.methodology}</p>
        </div>
      )}
    </div>
  );
}
