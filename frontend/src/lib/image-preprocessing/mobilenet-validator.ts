import type * as tf from "@tensorflow/tfjs";
import type { MobileNet } from "@tensorflow-models/mobilenet";

let modelPromise: Promise<MobileNet> | null = null;

const NON_MEDICAL_BLOCKLIST = [
  // Animals
  "dog", "cat", "bird", "fish", "horse", "cow", "sheep", "pig", "chicken",
  "hamster", "rabbit", "mouse", "rat", "parrot", "turtle", "snake", "lizard",
  "golden retriever", "labrador", "poodle", "bulldog", "beagle", "terrier",
  "tabby", "persian", "siamese", "kitten", "puppy",
  // Food & drink
  "pizza", "burger", "sandwich", "salad", "soup", "cake", "ice cream",
  "coffee", "beer", "wine", "fruit", "banana", "apple", "orange",
  "sushi", "pasta", "bread", "chocolate", "cookie", "donut",
  // Vehicles
  "car", "truck", "bus", "motorcycle", "bicycle", "boat", "airplane",
  "train", "taxi", "ambulance", "convertible", "minivan", "sports car",
  "limousine", "jeep", "sedan",
  // Nature & scenery
  "beach", "mountain", "forest", "sunset", "sunrise", "lake", "ocean",
  "flower", "garden", "park", "landscape", "waterfall",
  // People & clothing
  "jersey", "suit", "dress", "shirt", "hat", "sunglasses", "tie",
  "bikini", "jean", "sneaker", "sandal",
  // Electronics & objects
  "laptop", "phone", "television", "remote", "keyboard", "mouse pad",
  "headphone", "speaker", "camera", "game controller",
  // Furniture & household
  "chair", "table", "couch", "bed", "lamp", "clock", "vase",
  "bookcase", "desk", "pillow", "curtain",
];

const CONFIDENCE_THRESHOLD = 0.4;
const SATURATION_THRESHOLD = 0.35;

function matchesBlocklist(prediction: string): boolean {
  const lower = prediction.toLowerCase();
  return NON_MEDICAL_BLOCKLIST.some(
    (blocked) => lower.includes(blocked) || blocked.includes(lower)
  );
}

async function loadModel(): Promise<MobileNet> {
  if (!modelPromise) {
    modelPromise = (async () => {
      try {
        await import("@tensorflow/tfjs");
        const mobilenet = await import("@tensorflow-models/mobilenet");
        const model = await mobilenet.load({ version: 2, alpha: 1.0 });
        return model;
      } catch (err) {
        modelPromise = null;
        throw err;
      }
    })();
  }
  return modelPromise;
}

function computeSaturation(imageData: ImageData): number {
  const { data, width, height } = imageData;
  let totalSaturation = 0;
  const pixelCount = width * height;

  for (let i = 0; i < data.length; i += 4) {
    const r = data[i] / 255;
    const g = data[i + 1] / 255;
    const b = data[i + 2] / 255;

    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    const l = (max + min) / 2;

    if (max === min) {
      // achromatic
      continue;
    }

    const d = max - min;
    const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    totalSaturation += s;
  }

  return totalSaturation / pixelCount;
}

function imageToImageData(img: HTMLImageElement): ImageData {
  const canvas = document.createElement("canvas");
  // Use a smaller size for analysis to speed things up
  const maxDim = 512;
  let w = img.naturalWidth;
  let h = img.naturalHeight;
  if (w > maxDim || h > maxDim) {
    const scale = maxDim / Math.max(w, h);
    w = Math.round(w * scale);
    h = Math.round(h * scale);
  }
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d")!;
  ctx.drawImage(img, 0, 0, w, h);
  return ctx.getImageData(0, 0, w, h);
}

export interface ValidationResult {
  valid: boolean;
  prediction?: string;
  confidence?: number;
  reason?: string;
}

export async function validateMedicalImage(
  file: File,
  onProgress?: (progress: number) => void
): Promise<ValidationResult> {
  let model: MobileNet;

  try {
    onProgress?.(0.05);
    model = await loadModel();
    onProgress?.(0.25);
  } catch {
    // Graceful degradation: allow upload if model fails to load
    return { valid: true, reason: "Model unavailable, skipping validation" };
  }

  // Load image
  const img = await new Promise<HTMLImageElement>((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = reject;
    const url = URL.createObjectURL(file);
    image.src = url;
  });

  onProgress?.(0.30);

  // Classify
  const predictions = await model.classify(img);
  onProgress?.(0.40);

  // Check top prediction against blocklist
  const topPrediction = predictions[0];
  if (
    topPrediction &&
    topPrediction.probability > CONFIDENCE_THRESHOLD &&
    matchesBlocklist(topPrediction.className)
  ) {
    return {
      valid: false,
      prediction: topPrediction.className,
      confidence: topPrediction.probability,
      reason: `This doesn't appear to be a medical image. Detected: ${topPrediction.className}. Please upload X-rays, CT scans, MRI, or ultrasound images.`,
    };
  }

  onProgress?.(0.45);

  // Check saturation — medical images tend to be low-saturation / grayscale
  const imageData = imageToImageData(img);
  const avgSaturation = computeSaturation(imageData);

  // Revoke object URL
  URL.revokeObjectURL(img.src);

  onProgress?.(0.50);

  // High saturation is a soft signal — only flag if combined with a non-medical prediction
  if (
    avgSaturation > SATURATION_THRESHOLD &&
    topPrediction &&
    topPrediction.probability > 0.25 &&
    matchesBlocklist(topPrediction.className)
  ) {
    return {
      valid: false,
      prediction: topPrediction.className,
      confidence: topPrediction.probability,
      reason: `This doesn't appear to be a medical image. Detected: ${topPrediction.className}. Please upload X-rays, CT scans, MRI, or ultrasound images.`,
    };
  }

  return { valid: true };
}

export function isModelLoaded(): boolean {
  return modelPromise !== null;
}
