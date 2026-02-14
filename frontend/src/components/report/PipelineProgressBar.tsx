"use client";

import type { PipelineStep } from "@/lib/types";

interface Props {
  steps: PipelineStep[];
}

const STEP_ICONS: Record<string, JSX.Element> = {
  image_analysis: (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0 0 22.5 18.75V5.25A2.25 2.25 0 0 0 20.25 3H3.75A2.25 2.25 0 0 0 1.5 5.25v13.5A2.25 2.25 0 0 0 3.75 21Z" />
    </svg>
  ),
  research: (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
    </svg>
  ),
  report_generation: (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
    </svg>
  ),
  safety_review: (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
    </svg>
  ),
};

function getStepStyles(state: string) {
  switch (state) {
    case "complete":
      return { circle: "bg-green-500 text-white", line: "bg-green-500" };
    case "in_progress":
      return { circle: "bg-medical-600 text-white animate-pulse", line: "bg-gray-300" };
    case "failed":
      return { circle: "bg-red-500 text-white", line: "bg-gray-300" };
    case "skipped":
      return { circle: "bg-gray-300 text-gray-500", line: "bg-gray-300" };
    default:
      return { circle: "bg-gray-200 text-gray-400", line: "bg-gray-200" };
  }
}

export default function PipelineProgressBar({ steps }: Props) {
  return (
    <div className="flex items-center justify-between">
      {steps.map((step, i) => {
        const styles = getStepStyles(step.state);
        const isLast = i === steps.length - 1;

        return (
          <div key={step.id} className="flex flex-1 items-center">
            <div className="flex flex-col items-center">
              <div
                className={`flex h-10 w-10 items-center justify-center rounded-full ${styles.circle} transition-colors`}
              >
                {step.state === "complete" ? (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                ) : step.state === "failed" ? (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                  </svg>
                ) : (
                  STEP_ICONS[step.id] || <span className="text-xs">{i + 1}</span>
                )}
              </div>
              <span className="mt-2 text-xs font-medium text-gray-600">{step.label}</span>
            </div>
            {!isLast && (
              <div className={`mx-2 h-0.5 flex-1 rounded ${styles.line} transition-colors`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
