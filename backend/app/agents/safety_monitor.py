import json
import logging

from botocore.exceptions import ClientError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.report import Report
from app.models.safety_review import SafetyReview
from app.utils.bedrock_client import (
    converse_with_retry,
    get_bedrock_client,
    _extract_text,
    _get_error_message,
)

logger = logging.getLogger(__name__)

PRIMARY_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

SYSTEM_PROMPT = (
    "You are a medical AI safety monitor. Review this diagnostic report for: "
    "1) Potential hallucinations or unsupported claims that aren't backed by "
    "the provided research, 2) Demographic or diagnostic bias, "
    "3) Overconfident language that should include more uncertainty, "
    "4) Missing disclaimers. Return a JSON object with: flagged_issues "
    "(array of issues with severity and description), adjusted_confidence_score "
    "(0-1), recommended_disclaimers (array of strings), and safety_passed (boolean)."
)

REVIEW_PROMPT_TEMPLATE = (
    "Review the following diagnostic report for safety issues.\n\n"
    "## Final Report\n"
    "{final_report}\n\n"
    "## Original Findings\n"
    "{findings}\n\n"
    "## Supporting Research\n"
    "{research}\n\n"
    "Return your safety review as a JSON object."
)

GUARDRAIL_CONTENT_POLICY = {
    "filtersConfig": [
        {
            "type": "VIOLENCE",
            "inputStrength": "HIGH",
            "outputStrength": "HIGH",
        },
        {
            "type": "HATE",
            "inputStrength": "HIGH",
            "outputStrength": "HIGH",
        },
        {
            "type": "MISCONDUCT",
            "inputStrength": "HIGH",
            "outputStrength": "HIGH",
        },
    ],
    "wordPolicyConfig": {
        "managedWordListsConfig": [{"type": "PROFANITY"}],
    },
}


class SafetyAgent:
    """Agent that performs safety review on generated medical reports."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = get_bedrock_client()

    async def review(self, report: Report) -> Report:
        """Run the full safety review pipeline on a report."""
        if settings.demo_mode:
            from app.agents.demo_data import get_demo_safety_review, demo_delay

            await demo_delay()
            safety_result = get_demo_safety_review()
            guardrail_result = {"action": "NONE", "detail": "Demo mode — guardrails skipped"}
            await self._save_safety_review(report, safety_result, guardrail_result)
            report.safety_review = json.dumps(safety_result, indent=2)
            report.confidence_score = safety_result.get(
                "adjusted_confidence_score", report.confidence_score
            )
            report.status = "complete"
            logger.info("DEMO: safety review complete for report %s", report.id)
            await self.db.commit()
            await self.db.refresh(report)
            return report

        final_report = self._load_json_field(report.final_report, "final_report")
        findings = self._load_json_field(report.findings, "findings")
        research = self._load_json_field(report.research_results, "research_results")

        logger.info("Starting safety review for report %s", report.id)

        # Layer 1: Bedrock Guardrails
        guardrail_result = await self._apply_guardrails(report.final_report)

        # Layer 2: Claude safety review
        safety_result = await self._claude_safety_review(
            final_report, findings, research
        )

        # Merge guardrail findings into safety result
        if guardrail_result.get("action") == "GUARDRAIL_INTERVENED":
            safety_result["flagged_issues"].append({
                "severity": "high",
                "description": "Bedrock Guardrail flagged content — see guardrail_result for details.",
                "source": "bedrock_guardrail",
            })
            safety_result["safety_passed"] = False

        # Upsert SafetyReview record
        await self._save_safety_review(report, safety_result, guardrail_result)

        # Update report
        report.safety_review = json.dumps(safety_result, indent=2)
        report.confidence_score = safety_result.get(
            "adjusted_confidence_score", report.confidence_score
        )
        report.status = "complete"

        logger.info(
            "Safety review complete for report %s: passed=%s",
            report.id, safety_result.get("safety_passed"),
        )

        await self.db.commit()
        await self.db.refresh(report)
        return report

    # ------------------------------------------------------------------
    # Layer 1: Bedrock Guardrails
    # ------------------------------------------------------------------

    async def _apply_guardrails(self, report_text: str) -> dict:
        guardrail_id = settings.bedrock_guardrail_id
        guardrail_version = settings.bedrock_guardrail_version

        if not guardrail_id:
            logger.info("No Bedrock guardrail configured, skipping guardrail check")
            return {"action": "NONE", "detail": "No guardrail configured"}

        try:
            response = self.client.apply_guardrail(
                guardrailIdentifier=guardrail_id,
                guardrailVersion=guardrail_version,
                source="OUTPUT",
                content=[{"text": {"text": report_text}}],
            )
            action = response.get("action", "NONE")
            logger.info("Guardrail result: %s", action)
            return {
                "action": action,
                "outputs": response.get("outputs", []),
                "assessments": response.get("assessments", []),
            }
        except ClientError as e:
            logger.error("Bedrock Guardrail call failed: %s", e)
            return {
                "action": "ERROR",
                "detail": _get_error_message(e),
            }

    # ------------------------------------------------------------------
    # Layer 2: Claude safety review
    # ------------------------------------------------------------------

    async def _claude_safety_review(
        self,
        final_report: dict | list,
        findings: dict | list,
        research: dict | list,
    ) -> dict:
        prompt = REVIEW_PROMPT_TEMPLATE.format(
            final_report=json.dumps(final_report, indent=2),
            findings=json.dumps(findings, indent=2),
            research=json.dumps(research, indent=2),
        )

        message = {
            "role": "user",
            "content": [{"text": prompt}],
        }
        system = [{"text": SYSTEM_PROMPT}]
        inference_config = {"maxTokens": 4096, "temperature": 0.2}

        try:
            response = await converse_with_retry(
                self.client, PRIMARY_MODEL_ID, [message], system, inference_config
            )
            raw = _extract_text(response)
            return self._parse_safety_result(raw)
        except ClientError as e:
            logger.error("Claude safety review failed: %s", e)
            return {
                "flagged_issues": [{
                    "severity": "high",
                    "description": f"Safety review model call failed: {_get_error_message(e)}",
                    "source": "system",
                }],
                "adjusted_confidence_score": 0.0,
                "recommended_disclaimers": [
                    "This report could not be fully safety-reviewed. "
                    "Please consult a qualified healthcare professional."
                ],
                "safety_passed": False,
            }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    async def _save_safety_review(
        self,
        report: Report,
        safety_result: dict,
        guardrail_result: dict,
    ) -> SafetyReview:
        result = await self.db.execute(
            select(SafetyReview).where(SafetyReview.report_id == report.id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.flagged_issues = json.dumps(safety_result.get("flagged_issues", []))
            existing.adjusted_confidence_score = safety_result.get("adjusted_confidence_score")
            existing.recommended_disclaimers = json.dumps(safety_result.get("recommended_disclaimers", []))
            existing.safety_passed = safety_result.get("safety_passed", False)
            existing.guardrail_result = json.dumps(guardrail_result)
            return existing

        review = SafetyReview(
            report_id=report.id,
            flagged_issues=json.dumps(safety_result.get("flagged_issues", [])),
            adjusted_confidence_score=safety_result.get("adjusted_confidence_score"),
            recommended_disclaimers=json.dumps(safety_result.get("recommended_disclaimers", [])),
            safety_passed=safety_result.get("safety_passed", False),
            guardrail_result=json.dumps(guardrail_result),
        )
        self.db.add(review)
        return review

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_safety_result(raw: str) -> dict:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Could not parse safety review as JSON: %s", text[:500])
            return {
                "flagged_issues": [{
                    "severity": "medium",
                    "description": "Safety review returned unparseable output",
                    "raw_output": text[:1000],
                }],
                "adjusted_confidence_score": 0.5,
                "recommended_disclaimers": [
                    "This report has not been fully safety-reviewed."
                ],
                "safety_passed": False,
            }

        if isinstance(parsed, dict):
            for key in ("safety_review", "review", "result"):
                if key in parsed and isinstance(parsed[key], dict):
                    return parsed[key]

        if isinstance(parsed, dict):
            parsed.setdefault("flagged_issues", [])
            parsed.setdefault("adjusted_confidence_score", 0.5)
            parsed.setdefault("recommended_disclaimers", [])
            parsed.setdefault("safety_passed", len(parsed["flagged_issues"]) == 0)

        return parsed

    @staticmethod
    def _load_json_field(value: str | None, field_name: str) -> dict | list:
        if not value:
            raise ValueError(f"Report has no {field_name}")
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise ValueError(f"Cannot parse {field_name}: {e}")
