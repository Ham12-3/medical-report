import type { Finding, ResearchResult, FinalReport, SafetyReview } from "./types";

function safeParse<T>(json: string | null | undefined): T | null {
  if (!json) return null;
  try {
    return JSON.parse(json) as T;
  } catch {
    return null;
  }
}

export function parseFindings(raw: string | null | undefined): Finding[] {
  const parsed = safeParse<Finding[]>(raw);
  return Array.isArray(parsed) ? parsed : [];
}

export function parseResearch(raw: string | null | undefined): ResearchResult[] {
  const parsed = safeParse<ResearchResult[]>(raw);
  return Array.isArray(parsed) ? parsed : [];
}

export function parseFinalReport(raw: string | null | undefined): FinalReport | null {
  return safeParse<FinalReport>(raw);
}

export function parseSafetyReview(raw: string | null | undefined): SafetyReview | null {
  return safeParse<SafetyReview>(raw);
}
