// Parsed shapes for JSON fields stored in the report

export interface Finding {
  id: string;
  finding: string;
  location: string;
  severity: "critical" | "high" | "moderate" | "low" | "normal";
  confidence: number; // 0-1
  details: string;
}

export interface ResearchReference {
  title: string;
  source: string;
  url?: string;
  relevance_score: number; // 0-1
  summary: string;
}

export interface ResearchResult {
  finding_id: string;
  finding: string;
  references: ResearchReference[];
}

export interface FinalReport {
  executive_summary: string;
  detailed_findings: {
    finding: string;
    analysis: string;
    supporting_evidence: string;
    clinical_significance: string;
  }[];
  risk_assessment: {
    category: string;
    level: "critical" | "high" | "moderate" | "low";
    description: string;
  }[];
  next_steps: string[];
  methodology: string;
}

export interface SafetyReview {
  safety_passed: boolean;
  flagged_issues: string[];
  disclaimers: string[];
  adjusted_confidence_score: number | null;
  review_notes: string;
}

// Pipeline step tracking for the WebSocket hook
export type StepState = "pending" | "in_progress" | "complete" | "failed" | "skipped";

export interface PipelineStep {
  id: string;
  label: string;
  state: StepState;
}
