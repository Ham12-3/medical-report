"use client";

import type { PreprocessingProgress as ProgressData, PreprocessingStep } from "@/lib/image-preprocessing";

interface Props {
  progress: ProgressData;
}

const STEPS: { key: PreprocessingStep; label: string }[] = [
  { key: "loading-model", label: "Loading Model" },
  { key: "validating", label: "Validating" },
  { key: "enhancing", label: "Enhancing" },
  { key: "compressing", label: "Compressing" },
];

function getStepIndex(step: PreprocessingStep): number {
  return STEPS.findIndex((s) => s.key === step);
}

export default function PreprocessingProgress({ progress }: Props) {
  const currentIndex = getStepIndex(progress.step);

  return (
    <div className="flex flex-col items-center gap-3 py-2">
      {/* Step indicators */}
      <div className="flex items-center gap-1">
        {STEPS.map((step, i) => {
          const isComplete = i < currentIndex;
          const isCurrent = i === currentIndex;

          return (
            <div key={step.key} className="flex items-center">
              <div className="flex flex-col items-center">
                <div
                  className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-medium transition-colors ${
                    isComplete
                      ? "bg-teal-600 text-white"
                      : isCurrent
                        ? "bg-teal-100 text-teal-700 ring-2 ring-teal-500"
                        : "bg-gray-100 text-gray-400"
                  }`}
                >
                  {isComplete ? (
                    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    i + 1
                  )}
                </div>
                <span
                  className={`mt-1 text-[10px] leading-tight ${
                    isCurrent ? "font-medium text-teal-700" : "text-gray-400"
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div
                  className={`mx-1 mb-4 h-0.5 w-6 transition-colors ${
                    i < currentIndex ? "bg-teal-500" : "bg-gray-200"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Progress bar */}
      <div className="w-full overflow-hidden rounded-full bg-gray-100">
        <div
          className="h-1.5 rounded-full bg-teal-500 transition-all duration-300 ease-out"
          style={{ width: `${Math.round(progress.progress * 100)}%` }}
        />
      </div>

      {/* Status message */}
      <p className="text-sm text-gray-600">{progress.message}</p>
    </div>
  );
}
