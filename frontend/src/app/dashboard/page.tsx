"use client";

import ImageUpload from "@/components/ImageUpload";
import { useToast } from "@/components/Toast";
import ReportCardGrid from "@/components/dashboard/ReportCardGrid";
import { getReports, type Report } from "@/lib/api";
import { useCallback, useEffect, useState } from "react";

export default function DashboardPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState("");
  const { addToast } = useToast();

  const fetchReports = useCallback(async () => {
    setFetchError("");
    try {
      const data = await getReports();
      setReports(data);
    } catch (err: any) {
      const msg = err.message || "Failed to load reports";
      setFetchError(msg);
      addToast("error", msg);
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  function handleUploadComplete() {
    addToast("success", "Image uploaded successfully. Processing will begin shortly.");
    fetchReports();
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <section className="mb-8">
        <h2 className="mb-3 text-sm font-medium text-gray-700">
          Upload medical image
        </h2>
        <ImageUpload onUploadComplete={handleUploadComplete} />
      </section>

      <section>
        <h2 className="mb-4 text-sm font-medium text-gray-700">Your reports</h2>
        {fetchError && !loading ? (
          <div className="rounded-xl border border-red-200 bg-red-50 px-6 py-10 text-center">
            <svg
              className="mx-auto mb-3 h-10 w-10 text-red-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
              />
            </svg>
            <p className="mb-1 text-sm font-medium text-red-800">
              Failed to load reports
            </p>
            <p className="mb-4 text-sm text-red-600">{fetchError}</p>
            <button
              onClick={fetchReports}
              className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        ) : (
          <ReportCardGrid reports={reports} loading={loading} />
        )}
      </section>
    </main>
  );
}
