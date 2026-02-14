import json
import logging
from pathlib import Path

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
FALLBACK_MODEL_ID = "amazon.nova-pro-v1:0"

SYSTEM_PROMPT = (
    "You are a medical image analysis assistant. Analyze this medical image "
    "and identify all potential findings. For each finding provide: the finding "
    "name, location in the image, severity (low/medium/high), and confidence "
    "score (0-1). Return your analysis as structured JSON only, no preamble."
)

ANALYSIS_PROMPT = "Analyze this medical image and return structured JSON findings."

# Map file extensions to Bedrock-compatible image formats
EXT_TO_FORMAT = {
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".png": "png",
}


class ImageAnalysisAgent:
    """Agent that analyses a medical image via AWS Bedrock vision models."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = get_bedrock_client()

    async def analyze(self, report: Report) -> Report:
        """Run image analysis on a report's uploaded image."""
        if settings.demo_mode:
            from app.agents.demo_data import get_demo_findings, demo_delay

            await demo_delay()
            findings = get_demo_findings()
            report.findings = json.dumps(findings, indent=2)
            report.confidence_score = self._compute_confidence(findings)
            report.status = "image_analyzed"
            logger.info("DEMO: image analysis complete for report %s", report.id)
            await self.db.commit()
            await self.db.refresh(report)
            return report

        image_path = self._resolve_image_path(report.image_url)
        image_bytes = image_path.read_bytes()
        media_format = self._get_media_format(image_path)

        logger.info(
            "Starting image analysis for report %s (image: %s, %d bytes)",
            report.id, image_path.name, len(image_bytes),
        )

        message = self._build_message(image_bytes, media_format)
        system = [{"text": SYSTEM_PROMPT}]
        inference_config = {"maxTokens": 4096, "temperature": 0.2}

        try:
            raw_response = await self._call_bedrock(message, system, inference_config)
        except ClientError as e:
            logger.error("Image analysis failed for report %s: %s", report.id, e)
            report.status = "analysis_failed"
            await self.db.commit()
            await self.db.refresh(report)
            raise RuntimeError(_get_error_message(e)) from e

        findings = self._parse_findings(raw_response)
        confidence_score = self._compute_confidence(findings)

        report.findings = json.dumps(findings, indent=2)
        report.confidence_score = confidence_score
        report.status = "image_analyzed"

        logger.info(
            "Image analysis complete for report %s: %d findings, confidence=%.2f",
            report.id, len(findings), confidence_score,
        )

        await self.db.commit()
        await self.db.refresh(report)
        return report

    # ------------------------------------------------------------------
    # Bedrock interaction
    # ------------------------------------------------------------------

    def _build_message(self, image_bytes: bytes, media_format: str) -> dict:
        return {
            "role": "user",
            "content": [
                {
                    "image": {
                        "format": media_format,
                        "source": {"bytes": image_bytes},
                    },
                },
                {"text": ANALYSIS_PROMPT},
            ],
        }

    async def _call_bedrock(
        self, message: dict, system: list, inference_config: dict
    ) -> str:
        # Try primary model (Claude Sonnet 4.5) with retry
        try:
            response = await converse_with_retry(
                self.client, PRIMARY_MODEL_ID, [message], system, inference_config
            )
            return _extract_text(response)
        except ClientError as e:
            logger.warning(
                "Primary model (%s) failed, falling back: %s",
                PRIMARY_MODEL_ID, e,
            )

        # Fallback to Amazon Nova Pro with retry
        try:
            response = await converse_with_retry(
                self.client, FALLBACK_MODEL_ID, [message], system, inference_config
            )
            return _extract_text(response)
        except ClientError as e:
            logger.error(
                "Fallback model (%s) also failed: %s", FALLBACK_MODEL_ID, e
            )
            raise

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_image_path(image_url: str | None) -> Path:
        if not image_url:
            raise ValueError("Report has no image_url")
        filename = image_url.split("/")[-1]
        path = Path("/app/uploads") / filename
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")
        return path

    @staticmethod
    def _get_media_format(path: Path) -> str:
        ext = path.suffix.lower()
        fmt = EXT_TO_FORMAT.get(ext)
        if not fmt:
            raise ValueError(
                f"Unsupported image format '{ext}' for vision analysis. "
                "Supported: JPEG, PNG."
            )
        return fmt

    @staticmethod
    def _parse_findings(raw: str) -> list[dict]:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            logger.error("Failed to parse model response as JSON: %s", text[:500])
            return [
                {
                    "finding": "raw_analysis",
                    "details": text,
                    "severity": "unknown",
                    "confidence": 0.0,
                }
            ]

        if isinstance(parsed, dict):
            for key in ("findings", "results", "analysis"):
                if key in parsed and isinstance(parsed[key], list):
                    return parsed[key]
            return [parsed]

        if isinstance(parsed, list):
            return parsed

        return [parsed]

    @staticmethod
    def _compute_confidence(findings: list[dict]) -> float:
        scores = []
        for f in findings:
            score = f.get("confidence") or f.get("confidence_score")
            if score is not None:
                try:
                    scores.append(float(score))
                except (TypeError, ValueError):
                    pass
        return sum(scores) / len(scores) if scores else 0.0
