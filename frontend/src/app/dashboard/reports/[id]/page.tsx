"use client";

import { useParams, useSearchParams } from "next/navigation";
import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useReportPipeline } from "@/hooks/useReportPipeline";
import { parseFindings, parseResearch, parseFinalReport, parseSafetyReview } from "@/lib/report-parser";
import { getStatusConfig } from "@/lib/status-config";
import ReportStatusBadge from "@/components/report/ReportStatusBadge";
import ConfidenceIndicator from "@/components/report/ConfidenceIndicator";
import PipelineProgressBar from "@/components/report/PipelineProgressBar";
import MedicalImage from "@/components/report/MedicalImage";
import FindingsSection from "@/components/report/FindingsSection";
import ResearchSection from "@/components/report/ResearchSection";
import FinalReportSection from "@/components/report/FinalReportSection";
import SafetyReviewSection from "@/components/report/SafetyReviewSection";

export default function ReportDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const reportId = params.id as string;
  const autoGenerate = searchParams.get("generate") === "true";
  const hasTriggered = useRef(false);

  const {
    report,
    loading,
    error,
    steps,
    pipelineRunning,
    startPipeline,
    refreshReport,
  } = useReportPipeline(reportId);

  // Auto-start pipeline if ?generate=true and status is uploaded
  useEffect(() => {
    if (autoGenerate && report && report.status === "uploaded" && !hasTriggered.current) {
      hasTriggered.current = true;
      startPipeline();
    }
  }, [autoGenerate, report, startPipeline]);

  if (loading) {
    return (
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <div className="mb-6 flex items-center justify-between">
          <div className="h-4 w-16 animate-pulse rounded bg-gray-200" />
          <div className="h-6 w-24 animate-pulse rounded-full bg-gray-200" />
        </div>
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-1">
            <div className="aspect-square animate-pulse rounded-xl bg-gray-200" />
            <div className="space-y-3 rounded-xl border border-gray-200 bg-white p-5">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="h-3 w-20 animate-pulse rounded bg-gray-200" />
                  <div className="h-3 w-24 animate-pulse rounded bg-gray-200" />
                </div>
              ))}
            </div>
          </div>
          <div className="space-y-6 lg:col-span-2">
            {[1, 2].map((i) => (
              <div key={i} className="rounded-xl border border-gray-200 bg-white p-6">
                <div className="mb-4 h-5 w-32 animate-pulse rounded bg-gray-200" />
                <div className="space-y-2">
                  <div className="h-3 w-full animate-pulse rounded bg-gray-200" />
                  <div className="h-3 w-5/6 animate-pulse rounded bg-gray-200" />
                  <div className="h-3 w-4/6 animate-pulse rounded bg-gray-200" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    );
  }

  if (!report) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center">
        <p className="text-gray-500">Report not found.</p>
        <Link href="/dashboard" className="mt-4 inline-block text-sm text-medical-600 hover:underline">
          Back to dashboard
        </Link>
      </div>
    );
  }

  const findings = parseFindings(report.findings);
  const research = parseResearch(report.research_results);
  const finalReport = parseFinalReport(report.final_report);
  const safetyReview = parseSafetyReview(report.safety_review);
  const statusCfg = getStatusConfig(report.status);

  const showFindings = findings.length > 0;
  const showResearch = research.length > 0;
  const showFinalReport = finalReport !== null;
  const showSafety = safetyReview !== null;
  const isComplete = report.status === "complete";
  const isUploaded = report.status === "uploaded";

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      {/* Top bar */}
      <div className="mb-6 flex items-center justify-between">
        <Link
          href="/dashboard"
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
          </svg>
          Back
        </Link>
        <div className="flex items-center gap-3">
          <ReportStatusBadge status={report.status} />
          {isComplete && (
            <ExportPdfButtonLazy report={report} findings={findings} research={research} finalReport={finalReport} safetyReview={safetyReview} />
          )}
        </div>
      </div>

      {/* Error banner */}
      {(error || statusCfg.isError) && (
        <div className="mb-6 flex items-center justify-between rounded-lg bg-red-50 border border-red-200 p-4">
          <div className="flex items-center gap-2 text-sm text-red-700">
            <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
            </svg>
            {error || `Pipeline failed at: ${statusCfg.label}`}
          </div>
          <button
            onClick={() => {
              refreshReport();
              startPipeline();
            }}
            className="rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      )}

      {/* Pipeline progress */}
      {(pipelineRunning || (!isUploaded && !isComplete && !statusCfg.isError)) && (
        <div className="mb-8 rounded-xl border border-gray-200 bg-white p-6">
          <PipelineProgressBar steps={steps} />
        </div>
      )}

      {/* Two-column layout */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Left column — image & meta */}
        <div className="space-y-6 lg:col-span-1">
          <MedicalImage imageUrl={report.image_url} />

          <div className="rounded-xl border border-gray-200 bg-white p-5 space-y-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Status</span>
              <ReportStatusBadge status={report.status} />
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Confidence</span>
              <ConfidenceIndicator score={report.confidence_score} />
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Created</span>
              <span className="text-gray-700">
                {new Date(report.created_at).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Updated</span>
              <span className="text-gray-700">
                {new Date(report.updated_at).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
          </div>

          {/* Generate button for uploaded reports */}
          {isUploaded && !pipelineRunning && (
            <button
              onClick={startPipeline}
              className="w-full rounded-lg bg-medical-600 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-medical-700"
            >
              Generate Report
            </button>
          )}
        </div>

        {/* Right column — report sections */}
        <div className="space-y-8 lg:col-span-2">
          {showFindings && <FindingsSection findings={findings} />}
          {showResearch && <ResearchSection research={research} />}
          {showFinalReport && <FinalReportSection report={finalReport} />}
          {showSafety && <SafetyReviewSection review={safetyReview} />}

          {!showFindings && !showResearch && !showFinalReport && !showSafety && !pipelineRunning && (
            <div className="rounded-xl border-2 border-dashed border-gray-300 px-6 py-16 text-center">
              <svg className="mx-auto mb-4 h-12 w-12 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
              </svg>
              <p className="text-sm text-gray-500">
                No report data yet. Click &quot;Generate Report&quot; to start the analysis pipeline.
              </p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

// Lazy wrapper to avoid SSR issues with @react-pdf/renderer
function ExportPdfButtonLazy(props: any) {
  const [Component, setComponent] = useState<React.ComponentType<any> | null>(null);

  useEffect(() => {
    import("@/components/pdf/ExportPdfButton")
      .then((mod) => setComponent(() => mod.default))
      .catch(() => {
        // PDF module not available, silently skip
      });
  }, []);

  if (!Component) return null;
  return <Component {...props} />;
}
