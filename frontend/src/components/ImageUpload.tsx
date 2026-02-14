"use client";

import { uploadImage } from "@/lib/api";
import { useCallback, useState, type DragEvent, type ChangeEvent } from "react";
import { preprocessImage, type PreprocessingProgress as ProgressData } from "@/lib/image-preprocessing";
import PreprocessingProgress from "./PreprocessingProgress";
import { useToast } from "./Toast";

const ACCEPTED = ".jpg,.jpeg,.png,.dcm";
const MAX_SIZE = 10 * 1024 * 1024;

interface Props {
  onUploadComplete: () => void;
}

export default function ImageUpload({ onUploadComplete }: Props) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [preprocessing, setPreprocessing] = useState(false);
  const [preprocessProgress, setPreprocessProgress] = useState<ProgressData | null>(null);
  const [error, setError] = useState("");
  const { addToast } = useToast();

  const handleFile = useCallback(
    async (file: File) => {
      setError("");

      if (file.size > MAX_SIZE) {
        setError(`File too large. Maximum size is 10MB.`);
        return;
      }

      const validTypes = ["image/jpeg", "image/png", "application/dicom", "application/octet-stream"];
      const validExts = [".jpg", ".jpeg", ".png", ".dcm"];
      const ext = file.name.toLowerCase().slice(file.name.lastIndexOf("."));

      if (!validTypes.includes(file.type) && !validExts.includes(ext)) {
        setError("Invalid file type. Accepted: JPEG, PNG, DICOM.");
        return;
      }

      // Preprocessing pipeline
      setPreprocessing(true);
      setPreprocessProgress(null);

      let fileToUpload: File;
      try {
        const result = await preprocessImage(file, (update) => {
          setPreprocessProgress(update);
        });

        if (result.rejected) {
          setError(result.rejectionReason || "Image validation failed.");
          setPreprocessing(false);
          setPreprocessProgress(null);
          return;
        }

        fileToUpload = result.file;
      } catch {
        // If preprocessing fails entirely, use original file
        fileToUpload = file;
      }

      setPreprocessing(false);
      setPreprocessProgress(null);

      // Upload
      setUploading(true);
      try {
        await uploadImage(fileToUpload);
        onUploadComplete();
      } catch (err: any) {
        const msg = err.message || "Upload failed";
        setError(msg);
        addToast("error", msg);
      } finally {
        setUploading(false);
      }
    },
    [onUploadComplete]
  );

  function onDragOver(e: DragEvent) {
    e.preventDefault();
    setDragging(true);
  }

  function onDragLeave(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function onFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = "";
  }

  const busy = preprocessing || uploading;

  return (
    <div>
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={`relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-10 transition-colors ${
          dragging
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 hover:border-gray-400"
        }`}
      >
        {preprocessing && preprocessProgress ? (
          <div className="w-full max-w-sm">
            <PreprocessingProgress progress={preprocessProgress} />
          </div>
        ) : uploading ? (
          <div className="flex flex-col items-center gap-2">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
            <p className="text-sm text-gray-600">Uploading...</p>
          </div>
        ) : (
          <>
            <svg
              className="mb-3 h-10 w-10 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 16.5V9.75m0 0 3 3m-3-3-3 3M6.75 19.5a4.5 4.5 0 0 1-1.41-8.775 5.25 5.25 0 0 1 10.233-2.33 3 3 0 0 1 3.758 3.848A3.752 3.752 0 0 1 18 19.5H6.75Z"
              />
            </svg>
            <p className="mb-1 text-sm text-gray-600">
              <span className="font-medium text-blue-600">Click to upload</span>{" "}
              or drag and drop
            </p>
            <p className="text-xs text-gray-400">
              JPEG, PNG, or DICOM up to 10MB
            </p>
            <input
              type="file"
              accept={ACCEPTED}
              onChange={onFileChange}
              disabled={busy}
              className="absolute inset-0 cursor-pointer opacity-0"
            />
          </>
        )}
      </div>

      {error && (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
