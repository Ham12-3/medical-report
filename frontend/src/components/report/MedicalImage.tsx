"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Props {
  imageUrl: string | null;
}

export default function MedicalImage({ imageUrl }: Props) {
  const [zoomed, setZoomed] = useState(false);

  if (!imageUrl) {
    return (
      <div className="flex aspect-square items-center justify-center rounded-xl bg-gray-100">
        <span className="text-sm text-gray-400">No image</span>
      </div>
    );
  }

  const src = `${API_URL}${imageUrl}`;

  return (
    <>
      <div
        className="cursor-zoom-in overflow-hidden rounded-xl border border-gray-200 bg-gray-100"
        onClick={() => setZoomed(true)}
      >
        <img src={src} alt="Medical scan" className="h-full w-full object-contain" />
      </div>

      {/* Zoom modal */}
      {zoomed && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          onClick={() => setZoomed(false)}
        >
          <div className="relative max-h-[90vh] max-w-[90vw]">
            <img
              src={src}
              alt="Medical scan (zoomed)"
              className="max-h-[90vh] max-w-[90vw] rounded-lg object-contain"
            />
            <button
              onClick={() => setZoomed(false)}
              className="absolute -right-3 -top-3 flex h-8 w-8 items-center justify-center rounded-full bg-white text-gray-600 shadow-lg hover:text-gray-900"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </>
  );
}
