"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getReport, generateReportWs, type Report, type PipelineMessage } from "@/lib/api";
import type { PipelineStep, StepState } from "@/lib/types";

const INITIAL_STEPS: PipelineStep[] = [
  { id: "image_analysis", label: "Image Analysis", state: "pending" },
  { id: "research", label: "Research", state: "pending" },
  { id: "report_generation", label: "Report Generation", state: "pending" },
  { id: "safety_review", label: "Safety Review", state: "pending" },
];

export function useReportPipeline(reportId: string) {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [steps, setSteps] = useState<PipelineStep[]>(INITIAL_STEPS);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const updateStep = useCallback((stepId: string, state: StepState) => {
    setSteps((prev) =>
      prev.map((s) => (s.id === stepId ? { ...s, state } : s))
    );
  }, []);

  const refreshReport = useCallback(async () => {
    try {
      const data = await getReport(reportId);
      setReport(data);
      return data;
    } catch (err: any) {
      setError(err.message || "Failed to load report");
      return null;
    }
  }, [reportId]);

  // Initial fetch
  useEffect(() => {
    setLoading(true);
    refreshReport().finally(() => setLoading(false));
  }, [refreshReport]);

  const startPipeline = useCallback(() => {
    if (pipelineRunning) return;
    setPipelineRunning(true);
    setError(null);
    setSteps(INITIAL_STEPS);

    const ws = generateReportWs(
      reportId,
      (msg: PipelineMessage) => {
        switch (msg.type) {
          case "pipeline_started":
            break;
          case "status": {
            const step = msg.step;
            const status = msg.status;
            if (step && status) {
              if (status === "in_progress") {
                updateStep(step, "in_progress");
              } else if (status === "complete" || status === "completed") {
                updateStep(step, "complete");
              } else if (status === "failed") {
                updateStep(step, "failed");
              } else if (status === "skipped") {
                updateStep(step, "skipped");
              }
            }
            break;
          }
          case "pipeline_complete":
            setPipelineRunning(false);
            refreshReport();
            break;
          case "error":
            setError(msg.detail || "Pipeline error");
            setPipelineRunning(false);
            refreshReport();
            break;
        }
      },
      () => {
        setError("Connection lost");
        setPipelineRunning(false);
      },
      () => {
        setPipelineRunning(false);
      }
    );

    wsRef.current = ws;
  }, [reportId, pipelineRunning, updateStep, refreshReport]);

  // Cleanup websocket on unmount
  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  return {
    report,
    loading,
    error,
    steps,
    pipelineRunning,
    startPipeline,
    refreshReport,
  };
}
