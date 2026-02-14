"use client";

import {
  Document,
  Page,
  Text,
  View,
  StyleSheet,
} from "@react-pdf/renderer";
import type { Report } from "@/lib/api";
import type { Finding, ResearchResult, FinalReport, SafetyReview } from "@/lib/types";

const styles = StyleSheet.create({
  page: {
    padding: 40,
    fontFamily: "Helvetica",
    fontSize: 10,
    color: "#1a1a1a",
  },
  header: {
    marginBottom: 20,
    borderBottomWidth: 2,
    borderBottomColor: "#2563eb",
    paddingBottom: 10,
  },
  title: {
    fontSize: 20,
    fontFamily: "Helvetica-Bold",
    color: "#172554",
  },
  subtitle: {
    fontSize: 10,
    color: "#6b7280",
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 14,
    fontFamily: "Helvetica-Bold",
    color: "#1e3a8a",
    marginTop: 20,
    marginBottom: 8,
  },
  card: {
    backgroundColor: "#f9fafb",
    borderRadius: 4,
    padding: 10,
    marginBottom: 8,
  },
  label: {
    fontSize: 8,
    color: "#6b7280",
    textTransform: "uppercase",
    marginBottom: 2,
  },
  value: {
    fontSize: 10,
    color: "#1a1a1a",
  },
  summaryBox: {
    backgroundColor: "#eff6ff",
    borderLeftWidth: 3,
    borderLeftColor: "#2563eb",
    padding: 12,
    marginBottom: 12,
    borderRadius: 4,
  },
  riskItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    padding: 6,
    borderBottomWidth: 1,
    borderBottomColor: "#e5e7eb",
  },
  badge: {
    fontSize: 8,
    fontFamily: "Helvetica-Bold",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 3,
    textTransform: "uppercase",
  },
  disclaimer: {
    backgroundColor: "#eff6ff",
    padding: 8,
    borderRadius: 4,
    marginBottom: 4,
    fontSize: 9,
    color: "#1e40af",
  },
  flaggedIssue: {
    backgroundColor: "#fefce8",
    padding: 8,
    borderRadius: 4,
    marginBottom: 4,
    fontSize: 9,
    color: "#854d0e",
  },
  footer: {
    position: "absolute",
    bottom: 30,
    left: 40,
    right: 40,
    textAlign: "center",
    fontSize: 8,
    color: "#9ca3af",
    borderTopWidth: 1,
    borderTopColor: "#e5e7eb",
    paddingTop: 8,
  },
  stepItem: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 4,
  },
  stepNumber: {
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: "#dbeafe",
    textAlign: "center",
    lineHeight: 18,
    fontSize: 8,
    color: "#1d4ed8",
    marginRight: 8,
    fontFamily: "Helvetica-Bold",
  },
});

interface Props {
  report: Report;
  findings: Finding[];
  research: ResearchResult[];
  finalReport: FinalReport | null;
  safetyReview: SafetyReview | null;
}

export default function ReportPdfDocument({
  report,
  findings,
  research,
  finalReport,
  safetyReview,
}: Props) {
  const confidencePct =
    report.confidence_score != null
      ? `${Math.round(report.confidence_score * 100)}%`
      : "N/A";

  return (
    <Document>
      <Page size="A4" style={styles.page}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Medical Analysis Report</Text>
          <Text style={styles.subtitle}>
            Generated on{" "}
            {new Date(report.updated_at).toLocaleDateString("en-US", {
              month: "long",
              day: "numeric",
              year: "numeric",
            })}{" "}
            | Confidence: {confidencePct}
          </Text>
        </View>

        {/* Executive Summary */}
        {finalReport && (
          <>
            <Text style={styles.sectionTitle}>Executive Summary</Text>
            <View style={styles.summaryBox}>
              <Text style={styles.value}>{finalReport.executive_summary}</Text>
            </View>
          </>
        )}

        {/* Findings */}
        {findings.length > 0 && (
          <>
            <Text style={styles.sectionTitle}>Findings</Text>
            {findings.map((f, i) => (
              <View key={i} style={styles.card}>
                <View
                  style={{
                    flexDirection: "row",
                    justifyContent: "space-between",
                    marginBottom: 4,
                  }}
                >
                  <Text style={{ fontFamily: "Helvetica-Bold", fontSize: 10 }}>
                    {f.finding}
                  </Text>
                  <Text
                    style={[
                      styles.badge,
                      {
                        backgroundColor:
                          f.severity === "critical"
                            ? "#fee2e2"
                            : f.severity === "high"
                              ? "#ffedd5"
                              : f.severity === "moderate"
                                ? "#fef9c3"
                                : "#dcfce7",
                        color:
                          f.severity === "critical"
                            ? "#991b1b"
                            : f.severity === "high"
                              ? "#9a3412"
                              : f.severity === "moderate"
                                ? "#854d0e"
                                : "#166534",
                      },
                    ]}
                  >
                    {f.severity}
                  </Text>
                </View>
                <Text style={styles.label}>{f.location}</Text>
                <Text style={styles.value}>{f.details}</Text>
                <Text style={[styles.label, { marginTop: 4 }]}>
                  Confidence: {Math.round(f.confidence * 100)}%
                </Text>
              </View>
            ))}
          </>
        )}

        <Text style={styles.footer}>
          MedAI Report Generator — This report is AI-generated and for informational purposes only.
        </Text>
      </Page>

      {/* Page 2: Detailed Report + Research */}
      {(finalReport || research.length > 0) && (
        <Page size="A4" style={styles.page}>
          {/* Detailed Findings */}
          {finalReport?.detailed_findings &&
            finalReport.detailed_findings.length > 0 && (
              <>
                <Text style={styles.sectionTitle}>Detailed Analysis</Text>
                {finalReport.detailed_findings.map((df, i) => (
                  <View key={i} style={styles.card}>
                    <Text
                      style={{
                        fontFamily: "Helvetica-Bold",
                        fontSize: 10,
                        marginBottom: 4,
                      }}
                    >
                      {df.finding}
                    </Text>
                    <Text style={styles.value}>{df.analysis}</Text>
                    {df.clinical_significance && (
                      <>
                        <Text style={[styles.label, { marginTop: 4 }]}>
                          Clinical Significance
                        </Text>
                        <Text style={styles.value}>
                          {df.clinical_significance}
                        </Text>
                      </>
                    )}
                  </View>
                ))}
              </>
            )}

          {/* Risk Assessment */}
          {finalReport?.risk_assessment &&
            finalReport.risk_assessment.length > 0 && (
              <>
                <Text style={styles.sectionTitle}>Risk Assessment</Text>
                {finalReport.risk_assessment.map((r, i) => (
                  <View key={i} style={styles.riskItem}>
                    <Text style={styles.value}>{r.category}</Text>
                    <Text
                      style={[
                        styles.badge,
                        {
                          backgroundColor:
                            r.level === "critical"
                              ? "#fee2e2"
                              : r.level === "high"
                                ? "#ffedd5"
                                : r.level === "moderate"
                                  ? "#fef9c3"
                                  : "#dcfce7",
                          color:
                            r.level === "critical"
                              ? "#991b1b"
                              : r.level === "high"
                                ? "#9a3412"
                                : r.level === "moderate"
                                  ? "#854d0e"
                                  : "#166534",
                        },
                      ]}
                    >
                      {r.level}
                    </Text>
                  </View>
                ))}
              </>
            )}

          {/* Next Steps */}
          {finalReport?.next_steps && finalReport.next_steps.length > 0 && (
            <>
              <Text style={styles.sectionTitle}>Recommended Next Steps</Text>
              {finalReport.next_steps.map((step, i) => (
                <View key={i} style={styles.stepItem}>
                  <Text style={styles.stepNumber}>{i + 1}</Text>
                  <Text style={[styles.value, { flex: 1 }]}>{step}</Text>
                </View>
              ))}
            </>
          )}

          {/* Research */}
          {research.length > 0 && (
            <>
              <Text style={styles.sectionTitle}>Research References</Text>
              {research.map((group, gi) => (
                <View key={gi} style={{ marginBottom: 8 }}>
                  <Text
                    style={{
                      fontFamily: "Helvetica-Bold",
                      fontSize: 9,
                      color: "#1e40af",
                      marginBottom: 4,
                    }}
                  >
                    {group.finding}
                  </Text>
                  {group.references.map((ref, ri) => (
                    <View key={ri} style={styles.card}>
                      <Text
                        style={{
                          fontFamily: "Helvetica-Bold",
                          fontSize: 9,
                        }}
                      >
                        {ref.title}
                      </Text>
                      <Text style={styles.label}>
                        {ref.source} | Relevance:{" "}
                        {Math.round(ref.relevance_score * 100)}%
                      </Text>
                      <Text style={[styles.value, { fontSize: 9 }]}>
                        {ref.summary}
                      </Text>
                    </View>
                  ))}
                </View>
              ))}
            </>
          )}

          <Text style={styles.footer}>
            MedAI Report Generator — This report is AI-generated and for informational purposes only.
          </Text>
        </Page>
      )}

      {/* Page 3: Safety Review */}
      {safetyReview && (
        <Page size="A4" style={styles.page}>
          <Text style={styles.sectionTitle}>Safety Review</Text>
          <View
            style={[
              styles.card,
              {
                backgroundColor: safetyReview.safety_passed
                  ? "#f0fdf4"
                  : "#fef2f2",
              },
            ]}
          >
            <Text
              style={{
                fontFamily: "Helvetica-Bold",
                fontSize: 12,
                color: safetyReview.safety_passed ? "#166534" : "#991b1b",
              }}
            >
              {safetyReview.safety_passed
                ? "Safety Review Passed"
                : "Safety Issues Detected"}
            </Text>
          </View>

          {safetyReview.flagged_issues &&
            safetyReview.flagged_issues.length > 0 && (
              <>
                <Text style={[styles.label, { marginTop: 8, marginBottom: 4 }]}>
                  Flagged Issues
                </Text>
                {safetyReview.flagged_issues.map((issue, i) => (
                  <View key={i} style={styles.flaggedIssue}>
                    <Text>{issue}</Text>
                  </View>
                ))}
              </>
            )}

          {safetyReview.disclaimers &&
            safetyReview.disclaimers.length > 0 && (
              <>
                <Text style={[styles.label, { marginTop: 8, marginBottom: 4 }]}>
                  Disclaimers
                </Text>
                {safetyReview.disclaimers.map((d, i) => (
                  <View key={i} style={styles.disclaimer}>
                    <Text>{d}</Text>
                  </View>
                ))}
              </>
            )}

          {safetyReview.review_notes && (
            <>
              <Text style={[styles.label, { marginTop: 8, marginBottom: 4 }]}>
                Review Notes
              </Text>
              <View style={styles.card}>
                <Text style={styles.value}>{safetyReview.review_notes}</Text>
              </View>
            </>
          )}

          <Text style={styles.footer}>
            MedAI Report Generator — This report is AI-generated and for informational purposes only.
          </Text>
        </Page>
      )}
    </Document>
  );
}
