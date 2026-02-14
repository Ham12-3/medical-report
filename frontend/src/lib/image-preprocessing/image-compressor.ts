import imageCompression from "browser-image-compression";

export async function compressImage(
  file: File | Blob,
  onProgress?: (progress: number) => void
): Promise<File> {
  onProgress?.(0.75);

  const inputFile =
    file instanceof File
      ? file
      : new File([file], "enhanced.jpg", { type: file.type || "image/jpeg" });

  const originalSize = inputFile.size;

  const compressed = await imageCompression(inputFile, {
    maxSizeMB: 5,
    maxWidthOrHeight: 2048,
    initialQuality: 0.85,
    useWebWorker: true,
    fileType: "image/jpeg",
  });

  onProgress?.(0.95);

  // Only use compressed if it's actually smaller
  if (compressed.size < originalSize) {
    return new File([compressed], inputFile.name, {
      type: compressed.type,
    });
  }

  return inputFile;
}
