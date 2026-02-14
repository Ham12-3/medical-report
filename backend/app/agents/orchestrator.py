"""LangGraph orchestrator for the report generation pipeline.

Defines a StateGraph with four agent nodes:
  1. image_analysis  — analyse the uploaded medical image
  2. research        — research findings against the knowledge base
  3. report_generation — generate a structured diagnostic report
  4. safety_review   — review for hallucinations, bias, and safety

Conditional edges:
  - After image_analysis: if no findings → END (no_findings)
  - After safety_review: if safety_passed=false and retries < 2 →
    loop back to report_generation with feedback
"""

import json
import logging
from typing import Awaitable, Callable, Optional
from uuid import UUID

from langgraph.graph import END, StateGraph
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.image_analysis import ImageAnalysisAgent
from app.agents.report_generator import ReportGenerationAgent
from app.agents.research import ResearchAgent
from app.agents.safety_monitor import SafetyAgent
from app.models.report import Report

logger = logging.getLogger(__name__)

# Callback type: (step_name, step_status) -> None
StatusCallback = Callable[[str, str], Awaitable[None]]

MAX_SAFETY_RETRIES = 2


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

async def _get_report(db: AsyncSession, report_id: str) -> Report:
    result = await db.execute(
        select(Report).where(Report.id == UUID(report_id))
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise ValueError(f"Report {report_id} not found")
    return report


async def _notify(
    callback: Optional[StatusCallback], step: str, status: str
) -> None:
    if callback:
        try:
            await callback(step, status)
        except Exception:
            pass


# ------------------------------------------------------------------
# Node functions
# ------------------------------------------------------------------

async def image_analysis_node(state: dict, config: dict) -> dict:
    db: AsyncSession = config["configurable"]["db"]
    callback: Optional[StatusCallback] = config["configurable"].get(
        "status_callback"
    )

    await _notify(callback, "image_analysis", "in_progress")

    report = await _get_report(db, state["report_id"])

    if report.status != "uploaded":
        # Already past this stage — check existing findings
        await _notify(callback, "image_analysis", "skipped")
        findings = json.loads(report.findings) if report.findings else []
        return {"has_findings": len(findings) > 0, "status": report.status}

    agent = ImageAnalysisAgent(db)
    report = await agent.analyze(report)

    findings = json.loads(report.findings) if report.findings else []
    has_findings = len(findings) > 0

    status_msg = "complete" if has_findings else "no_findings"
    await _notify(callback, "image_analysis", status_msg)

    return {"has_findings": has_findings, "status": report.status}


async def research_node(state: dict, config: dict) -> dict:
    db: AsyncSession = config["configurable"]["db"]
    callback: Optional[StatusCallback] = config["configurable"].get(
        "status_callback"
    )

    await _notify(callback, "research", "in_progress")

    report = await _get_report(db, state["report_id"])

    if report.status != "image_analyzed":
        await _notify(callback, "research", "skipped")
        return {"status": report.status}

    agent = ResearchAgent(db)
    report = await agent.research(report)

    await _notify(callback, "research", "complete")
    return {"status": report.status}


async def report_generation_node(state: dict, config: dict) -> dict:
    db: AsyncSession = config["configurable"]["db"]
    callback: Optional[StatusCallback] = config["configurable"].get(
        "status_callback"
    )

    retry_count = state.get("retry_count", 0)
    step_label = "report_generation"
    if retry_count > 0:
        step_label = f"report_generation_retry_{retry_count}"

    await _notify(callback, step_label, "in_progress")

    report = await _get_report(db, state["report_id"])

    # On retry after safety failure, reset status so the agent can run
    if retry_count > 0 and report.status == "complete":
        report.status = "report_generated"
        await db.commit()
        await db.refresh(report)

    if report.status not in ("research_complete", "report_generated"):
        await _notify(callback, step_label, "skipped")
        return {"status": report.status}

    agent = ReportGenerationAgent(db)
    safety_feedback = state.get("safety_feedback")
    report = await agent.generate(report, safety_feedback=safety_feedback)

    await _notify(callback, step_label, "complete")
    return {"status": report.status, "safety_feedback": None}


async def safety_review_node(state: dict, config: dict) -> dict:
    db: AsyncSession = config["configurable"]["db"]
    callback: Optional[StatusCallback] = config["configurable"].get(
        "status_callback"
    )

    await _notify(callback, "safety_review", "in_progress")

    report = await _get_report(db, state["report_id"])

    if report.status != "report_generated":
        await _notify(callback, "safety_review", "skipped")
        return {"status": report.status, "safety_passed": True}

    agent = SafetyAgent(db)
    report = await agent.review(report)

    # Determine whether safety passed
    safety_passed = True
    safety_feedback = None
    if report.safety_review:
        try:
            review_data = json.loads(report.safety_review)
            safety_passed = review_data.get("safety_passed", True)
            if not safety_passed:
                safety_feedback = report.safety_review
        except json.JSONDecodeError:
            safety_passed = False
            safety_feedback = report.safety_review

    status_msg = "complete" if safety_passed else "failed"
    await _notify(callback, "safety_review", status_msg)

    return {
        "status": report.status,
        "safety_passed": safety_passed,
        "safety_feedback": safety_feedback,
    }


async def increment_retry_node(state: dict, config: dict) -> dict:
    return {"retry_count": state.get("retry_count", 0) + 1}


# ------------------------------------------------------------------
# Conditional edge functions
# ------------------------------------------------------------------

def after_image_analysis(state: dict) -> str:
    if not state.get("has_findings", True):
        return "no_findings"
    return "research"


def after_safety_review(state: dict) -> str:
    if not state.get("safety_passed", True):
        retry_count = state.get("retry_count", 0)
        if retry_count < MAX_SAFETY_RETRIES:
            return "retry_report"
    return "done"


# ------------------------------------------------------------------
# Graph construction
# ------------------------------------------------------------------

def build_pipeline_graph():
    """Build and compile the LangGraph pipeline."""
    workflow = StateGraph(dict)

    # Nodes
    workflow.add_node("image_analysis", image_analysis_node)
    workflow.add_node("research", research_node)
    workflow.add_node("report_generation", report_generation_node)
    workflow.add_node("safety_review", safety_review_node)
    workflow.add_node("increment_retry", increment_retry_node)

    # Entry
    workflow.set_entry_point("image_analysis")

    # Edges
    workflow.add_conditional_edges(
        "image_analysis",
        after_image_analysis,
        {
            "no_findings": END,
            "research": "research",
        },
    )
    workflow.add_edge("research", "report_generation")
    workflow.add_edge("report_generation", "safety_review")
    workflow.add_conditional_edges(
        "safety_review",
        after_safety_review,
        {
            "retry_report": "increment_retry",
            "done": END,
        },
    )
    workflow.add_edge("increment_retry", "report_generation")

    return workflow.compile()


# Module-level compiled graph (built once, reused across requests)
_compiled_graph = None


def get_pipeline():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_pipeline_graph()
    return _compiled_graph


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

async def run_pipeline(
    report_id: str,
    db: AsyncSession,
    status_callback: Optional[StatusCallback] = None,
) -> dict:
    """Run the full report generation pipeline.

    Returns the final LangGraph state dict with keys like
    ``status``, ``has_findings``, ``safety_passed``, ``retry_count``.
    """
    pipeline = get_pipeline()

    initial_state = {
        "report_id": report_id,
        "status": "pending",
        "error": None,
        "retry_count": 0,
        "safety_passed": None,
        "has_findings": None,
        "safety_feedback": None,
    }

    config = {
        "configurable": {
            "db": db,
            "status_callback": status_callback,
        }
    }

    return await pipeline.ainvoke(initial_state, config=config)
