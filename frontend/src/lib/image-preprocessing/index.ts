import { validateMedicalImage, isModelLoaded } from "./mobilenet-validator";
import { enhanceImage } from "./canvas-enhancer";
import { compressImage } from "./image-compressor";

export type PreprocessingStep = "loading-model" | "validating" | "enhancing" | "compressing";

export interface PreprocessingProgress {
  step: PreprocessingStep;
  progress: number; // 0–1
  message: string;
}

export interface PreprocessingResult {
  file: File;
  rejected?: boolean;
  rejectionReason?: string;
}

function isDicom(file: File): boolean {
  const ext = file.name.toLowerCase();
  return ext.endsWith(".dcm") || file.type === "application/dicom";
}

export async function preprocessImage(
  file: File,
  onProgress?: (update: PreprocessingProgress) => void
): Promise<PreprocessingResult> {
  // Skip preprocessing for DICOM files
  if (isDicom(file)) {
    return { file };
  }

  // Step 1: Load model (show step only if not already loaded)
  if (!isModelLoaded()) {
    onProgress?.({
      step: "loading-model",
      progress: 0,
      message: "Loading AI model...",
    });
  }

  // Step 2: Validate
  onProgress?.({
    step: "validating",
    progress: 0.25,
    message: "Validating medical image...",
  });

  const validation = await validateMedicalImage(file, (p) => {
    onProgress?.({
      step: p < 0.25 ? "loading-model" : "validating",
      progress: p,
      message: p < 0.25 ? "Loading AI model..." : "Validating medical image...",
    });
  });

  if (!validation.valid) {
    return {
      file,
      rejected: true,
      rejectionReason: validation.reason,
    };
  }

  // Step 3: Enhance
  onProgress?.({
    step: "enhancing",
    progress: 0.50,
    message: "Enhancing image quality...",
  });

  let enhanced: Blob;
  try {
    enhanced = await enhanceImage(file, (p) => {
      onProgress?.({
        step: "enhancing",
        progress: p,
        message: "Enhancing image quality...",
      });
    });
  } catch {
    // Graceful degradation: use original if enhancement fails
    enhanced = file;
  }

  // Step 4: Compress
  onProgress?.({
    step: "compressing",
    progress: 0.75,
    message: "Optimizing for upload...",
  });

  let result: File;
  try {
    result = await compressImage(enhanced, (p) => {
      onProgress?.({
        step: "compressing",
        progress: p,
        message: "Optimizing for upload...",
      });
    });
  } catch {
    // Graceful degradation: use enhanced/original if compression fails
    result =
      enhanced instanceof File
        ? enhanced
        : new File([enhanced], file.name, { type: enhanced.type || file.type });
  }

  onProgress?.({
    step: "compressing",
    progress: 1,
    message: "Ready to upload",
  });

  return { file: result };
}
