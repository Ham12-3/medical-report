"use client";

import type { SafetyReview } from "@/lib/types";

interface Props {
  review: SafetyReview;
}

export default function SafetyReviewSection({ review }: Props) {
  return (
    <div>
      <h3 className="mb-4 text-lg font-semibold text-gray-900">Safety Review</h3>

      {/* Pass/fail banner */}
      <div
        className={`mb-4 flex items-center gap-3 rounded-lg p-4 ${
          review.safety_passed
            ? "bg-green-50 text-green-800"
            : "bg-red-50 text-red-800"
        }`}
      >
        {review.safety_passed ? (
          <svg className="h-6 w-6 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          </svg>
        ) : (
          <svg className="h-6 w-6 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
          </svg>
        )}
        <span className="font-medium">
          {review.safety_passed ? "Safety review passed" : "Safety issues detected"}
        </span>
      </div>

      {/* Flagged issues */}
      {review.flagged_issues && review.flagged_issues.length > 0 && (
        <div className="mb-4 space-y-2">
          <h4 className="text-sm font-semibold text-gray-700">Flagged Issues</h4>
          {review.flagged_issues.map((issue, i) => (
            <div
              key={i}
              className="rounded-lg bg-yellow-50 border border-yellow-200 p-3 text-sm text-yellow-800"
            >
              {issue}
            </div>
          ))}
        </div>
      )}

      {/* Disclaimers */}
      {review.disclaimers && review.disclaimers.length > 0 && (
        <div className="rounded-lg bg-blue-50 border border-blue-200 p-4">
          <h4 className="mb-2 text-sm font-semibold text-blue-800">Disclaimers</h4>
          <ul className="space-y-1">
            {review.disclaimers.map((d, i) => (
              <li key={i} className="text-sm text-blue-700">
                {d}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Review notes */}
      {review.review_notes && (
        <div className="mt-4 rounded-lg bg-gray-50 p-4">
          <h4 className="mb-1 text-sm font-semibold text-gray-600">Review Notes</h4>
          <p className="text-sm text-gray-600">{review.review_notes}</p>
        </div>
      )}
    </div>
  );
}
