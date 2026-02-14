import json
import logging

from botocore.exceptions import ClientError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.report import Report
from app.utils.bedrock_client import (
    converse_with_retry,
    get_bedrock_client,
    _extract_text,
    _get_error_message,
)

logger = logging.getLogger(__name__)

PRIMARY_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

SYSTEM_PROMPT = (
    "You are a medical report generator. Given the image analysis findings "
    "and supporting research, generate a professional diagnostic report. "
    "The report should include: an executive summary, detailed findings "
    "section with each finding explained alongside supporting literature, "
    "a risk assessment with overall confidence score, and recommended next "
    "steps. Format the report as structured JSON with sections."
)

REPORT_PROMPT_TEMPLATE = (
    "Generate a professional diagnostic report from the following data.\n\n"
    "## Image Analysis Findings\n"
    "{findings}\n\n"
    "## Supporting Research\n"
    "{research}\n\n"
    "Return the report as structured JSON with the following sections:\n"
    "- executive_summary\n"
    "- detailed_findings (array, each with finding, explanation, supporting_literature)\n"
    "- risk_assessment (overall_risk_level, confidence_score, key_risk_factors)\n"
    "- recommended_next_steps (array of actionable recommendations)\n"
    "- metadata (generated_at, model_used, disclaimer)\n"
)


class ReportGenerationAgent:
    """Agent that generates a professional diagnostic report."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = get_bedrock_client()

    async def generate(
        self, report: Report, safety_feedback: str | None = None
    ) -> Report:
        """Generate the final diagnostic report."""
        if settings.demo_mode:
            from app.agents.demo_data import get_demo_report, demo_delay

            await demo_delay()
            demo_report = get_demo_report()
            confidence = self._extract_confidence(demo_report, report.confidence_score)
            report.final_report = json.dumps(demo_report, indent=2)
            report.confidence_score = confidence
            report.status = "report_generated"
            logger.info("DEMO: report generation complete for report %s", report.id)
            await self.db.commit()
            await self.db.refresh(report)
            return report

        findings_json = self._load_json_field(report.findings, "findings")
        research_json = self._load_json_field(report.research_results, "research_results")

        logger.info("Starting report generation for report %s", report.id)

        prompt = REPORT_PROMPT_TEMPLATE.format(
            findings=json.dumps(findings_json, indent=2),
            research=json.dumps(research_json, indent=2),
        )

        if safety_feedback:
            prompt += (
                "\n\n## Safety Review Feedback\n"
                "A previous version of this report was flagged by safety review. "
                "Please address the following issues in your revised report:\n"
                f"{safety_feedback}\n"
            )

        try:
            raw_response = await self._call_bedrock(prompt)
        except ClientError as e:
            logger.error("Report generation failed for report %s: %s", report.id, e)
            report.status = "generation_failed"
            await self.db.commit()
            await self.db.refresh(report)
            raise RuntimeError(_get_error_message(e)) from e

        final_report = self._parse_report(raw_response)
        confidence = self._extract_confidence(final_report, report.confidence_score)

        report.final_report = json.dumps(final_report, indent=2)
        report.confidence_score = confidence
        report.status = "report_generated"

        logger.info(
            "Report generation complete for report %s, confidence=%.2f",
            report.id, confidence,
        )

        await self.db.commit()
        await self.db.refresh(report)
        return report

    # ------------------------------------------------------------------
    # Bedrock interaction
    # ------------------------------------------------------------------

    async def _call_bedrock(self, prompt: str) -> str:
        message = {
            "role": "user",
            "content": [{"text": prompt}],
        }
        system = [{"text": SYSTEM_PROMPT}]
        inference_config = {"maxTokens": 8192, "temperature": 0.3}

        response = await converse_with_retry(
            self.client, PRIMARY_MODEL_ID, [message], system, inference_config
        )
        return _extract_text(response)

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_report(raw: str) -> dict:
        text = raw.strip()

        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Could not parse report as JSON, wrapping raw text")
            parsed = {
                "executive_summary": "Report generation produced unstructured output.",
                "raw_report": text,
                "detailed_findings": [],
                "risk_assessment": {
                    "overall_risk_level": "unknown",
                    "confidence_score": 0.0,
                    "key_risk_factors": [],
                },
                "recommended_next_steps": [
                    "Review the raw report output manually."
                ],
            }

        if isinstance(parsed, dict):
            for key in ("report", "diagnostic_report", "result"):
                if key in parsed and isinstance(parsed[key], dict):
                    return parsed[key]

        return parsed

    @staticmethod
    def _extract_confidence(report_data: dict, current: float | None) -> float:
        risk = report_data.get("risk_assessment", {})
        score = risk.get("confidence_score")
        if score is not None:
            try:
                return float(score)
            except (TypeError, ValueError):
                pass
        return current or 0.0

    @staticmethod
    def _load_json_field(value: str | None, field_name: str) -> list | dict:
        if not value:
            raise ValueError(f"Report has no {field_name}")
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise ValueError(f"Cannot parse {field_name}: {e}")
