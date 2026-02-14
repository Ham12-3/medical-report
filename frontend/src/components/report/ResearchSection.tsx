"use client";

import type { ResearchResult } from "@/lib/types";

interface Props {
  research: ResearchResult[];
}

export default function ResearchSection({ research }: Props) {
  if (research.length === 0) return null;

  return (
    <div>
      <h3 className="mb-4 text-lg font-semibold text-gray-900">Research</h3>
      <div className="space-y-6">
        {research.map((group, gi) => (
          <div key={group.finding_id || gi}>
            <h4 className="mb-3 text-sm font-semibold text-medical-800">
              {group.finding}
            </h4>
            <div className="space-y-3">
              {group.references.map((ref, ri) => {
                const relPct = Math.round(ref.relevance_score * 100);
                return (
                  <div
                    key={ri}
                    className="rounded-lg border border-gray-200 bg-white p-4"
                  >
                    <div className="mb-1 flex items-start justify-between gap-2">
                      <h5 className="text-sm font-medium text-gray-900">
                        {ref.url ? (
                          <a
                            href={ref.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-medical-600 hover:underline"
                          >
                            {ref.title}
                          </a>
                        ) : (
                          ref.title
                        )}
                      </h5>
                      <span className="shrink-0 rounded bg-medical-50 px-2 py-0.5 text-xs font-medium text-medical-700">
                        {relPct}% relevant
                      </span>
                    </div>
                    <p className="mb-1 text-xs text-gray-500">{ref.source}</p>
                    <p className="text-sm text-gray-700">{ref.summary}</p>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
