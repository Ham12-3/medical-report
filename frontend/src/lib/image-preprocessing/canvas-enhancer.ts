export async function enhanceImage(
  file: File,
  onProgress?: (progress: number) => void
): Promise<Blob> {
  onProgress?.(0.50);

  const img = await new Promise<HTMLImageElement>((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = reject;
    image.src = URL.createObjectURL(file);
  });

  const canvas = document.createElement("canvas");
  canvas.width = img.naturalWidth;
  canvas.height = img.naturalHeight;
  const ctx = canvas.getContext("2d")!;
  ctx.drawImage(img, 0, 0);

  URL.revokeObjectURL(img.src);

  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const { data } = imageData;

  onProgress?.(0.55);

  // Compute pixel stats (luminance channel)
  let min = 255;
  let max = 0;
  let sum = 0;
  const pixelCount = canvas.width * canvas.height;

  for (let i = 0; i < data.length; i += 4) {
    const lum = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
    if (lum < min) min = lum;
    if (lum > max) max = lum;
    sum += lum;
  }

  const mean = sum / pixelCount;

  onProgress?.(0.60);

  // Adaptive contrast stretch: map [min, max] → [0, 255]
  const range = max - min;
  const contrastScale = range > 10 ? 255 / range : 1;

  // Brightness normalization: target mean ~120, capped ±40
  const targetMean = 120;
  const rawShift = targetMean - mean;
  const brightnessShift = Math.max(-40, Math.min(40, rawShift));

  for (let i = 0; i < data.length; i += 4) {
    for (let c = 0; c < 3; c++) {
      let val = data[i + c];
      // Contrast stretch
      if (range > 10) {
        val = (val - min) * contrastScale;
      }
      // Brightness shift
      val += brightnessShift;
      data[i + c] = Math.max(0, Math.min(255, Math.round(val)));
    }
    // Alpha unchanged
  }

  onProgress?.(0.70);

  ctx.putImageData(imageData, 0, 0);

  const blob = await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(
      (b) => (b ? resolve(b) : reject(new Error("Canvas toBlob failed"))),
      "image/jpeg",
      0.95
    );
  });

  onProgress?.(0.75);

  return blob;
}
