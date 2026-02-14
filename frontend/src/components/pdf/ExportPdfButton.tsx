"use client";

import { useState } from "react";
import { pdf } from "@react-pdf/renderer";
import ReportPdfDocument from "./ReportPdfDocument";
import type { Report } from "@/lib/api";
import type { Finding, ResearchResult, FinalReport, SafetyReview } from "@/lib/types";

interface Props {
  report: Report;
  findings: Finding[];
  research: ResearchResult[];
  finalReport: FinalReport | null;
  safetyReview: SafetyReview | null;
}

export default function ExportPdfButton({
  report,
  findings,
  research,
  finalReport,
  safetyReview,
}: Props) {
  const [generating, setGenerating] = useState(false);

  async function handleExport() {
    setGenerating(true);
    try {
      const blob = await pdf(
        <ReportPdfDocument
          report={report}
          findings={findings}
          research={research}
          finalReport={finalReport}
          safetyReview={safetyReview}
        />
      ).toBlob();

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `medical-report-${report.id.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("PDF generation failed:", err);
    } finally {
      setGenerating(false);
    }
  }

  return (
    <button
      onClick={handleExport}
      disabled={generating}
      className="inline-flex items-center gap-2 rounded-lg bg-medical-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-medical-700 disabled:opacity-50"
    >
      {generating ? (
        <>
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
          Generating...
        </>
      ) : (
        <>
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
          Export as PDF
        </>
      )}
    </button>
  );
}
