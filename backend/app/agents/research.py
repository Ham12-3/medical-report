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
from app.utils.embeddings import generate_embedding
from app.utils.pinecone_client import query_pinecone

logger = logging.getLogger(__name__)

PRIMARY_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

QUERY_GEN_SYSTEM = (
    "You are a medical research assistant. Given a clinical finding from a "
    "medical image analysis, generate 1-3 concise search queries that would "
    "retrieve relevant medical literature, clinical guidelines, or reference "
    "material about this finding. Return a JSON array of query strings only, "
    "no preamble."
)

PINECONE_NAMESPACE = "medical"
TOP_K = 3


class ResearchAgent:
    """Agent that researches medical findings against a Pinecone knowledge base."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = get_bedrock_client()

    async def research(self, report: Report) -> Report:
        """Run research on all findings in a report."""
        findings = self._load_findings(report)

        if settings.demo_mode:
            from app.agents.demo_data import get_demo_research, demo_delay

            await demo_delay()
            research_results = get_demo_research(findings)
            report.research_results = json.dumps(research_results, indent=2)
            report.status = "research_complete"
            logger.info("DEMO: research complete for report %s", report.id)
            await self.db.commit()
            await self.db.refresh(report)
            return report

        logger.info(
            "Starting research for report %s: %d findings",
            report.id, len(findings),
        )

        all_results = []
        for finding in findings:
            finding_name = self._extract_finding_name(finding)
            logger.info("Researching finding: %s", finding_name)

            try:
                queries = await self._generate_search_queries(finding)
            except Exception as e:
                logger.error(
                    "Query generation failed for finding '%s': %s",
                    finding_name, e,
                )
                queries = [
                    f"{finding_name} clinical guidelines",
                    f"{finding_name} medical literature",
                ]

            references = await self._search_knowledge_base(queries)

            all_results.append({
                "finding": finding_name,
                "search_queries": queries,
                "references": references,
            })

        report.research_results = json.dumps(all_results, indent=2)
        report.status = "research_complete"

        logger.info("Research complete for report %s", report.id)

        await self.db.commit()
        await self.db.refresh(report)
        return report

    # ------------------------------------------------------------------
    # Query generation via Claude
    # ------------------------------------------------------------------

    async def _generate_search_queries(self, finding: dict) -> list[str]:
        """Use Claude to generate search queries from a finding."""
        finding_text = json.dumps(finding, indent=2)
        prompt = (
            f"Generate search queries for this medical finding:\n\n{finding_text}"
        )

        message = {
            "role": "user",
            "content": [{"text": prompt}],
        }
        system = [{"text": QUERY_GEN_SYSTEM}]
        inference_config = {"maxTokens": 1024, "temperature": 0.2}

        try:
            response = await converse_with_retry(
                self.client, PRIMARY_MODEL_ID, [message], system, inference_config
            )
            raw = _extract_text(response)
            return self._parse_queries(raw)
        except ClientError as e:
            logger.error("Query generation failed: %s", e)
            # Fallback: use the finding name directly as a query
            name = self._extract_finding_name(finding)
            return [f"{name} clinical guidelines", f"{name} medical literature"]

    # ------------------------------------------------------------------
    # Pinecone search
    # ------------------------------------------------------------------

    async def _search_knowledge_base(self, queries: list[str]) -> list[dict]:
        """Embed each query, search Pinecone, deduplicate, return top results."""
        seen_ids: set[str] = set()
        references: list[dict] = []

        for query in queries:
            try:
                vector = await generate_embedding(query)
            except Exception as e:
                logger.error("Embedding failed for query '%s': %s", query, e)
                continue

            try:
                matches = query_pinecone(
                    vector=vector,
                    top_k=TOP_K,
                    namespace=PINECONE_NAMESPACE,
                )
            except Exception as e:
                logger.error("Pinecone query failed for '%s': %s", query, e)
                continue

            for match in matches:
                if match["id"] in seen_ids:
                    continue
                seen_ids.add(match["id"])
                references.append({
                    "id": match["id"],
                    "score": round(match["score"], 4),
                    "text": match["metadata"].get("text", ""),
                    "source_file": match["metadata"].get("source_file", ""),
                    "query_used": query,
                })

        # Sort by score descending and keep top 3
        references.sort(key=lambda r: r["score"], reverse=True)
        return references[:TOP_K]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_findings(report: Report) -> list[dict]:
        if not report.findings:
            raise ValueError("Report has no findings to research")
        try:
            findings = json.loads(report.findings)
        except json.JSONDecodeError as e:
            raise ValueError(f"Cannot parse report findings: {e}")
        if not isinstance(findings, list):
            findings = [findings]
        return findings

    @staticmethod
    def _extract_finding_name(finding: dict) -> str:
        for key in ("finding", "name", "finding_name", "title"):
            if key in finding and finding[key]:
                return str(finding[key])
        return "unknown finding"

    @staticmethod
    def _parse_queries(raw: str) -> list[str]:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Could not parse query response as JSON: %s", text[:300])
            return [line.strip().strip('"').strip("'") for line in text.split("\n") if line.strip()]

        if isinstance(parsed, list):
            return [str(q) for q in parsed if q]
        return [str(parsed)]
