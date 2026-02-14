import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.image_analysis import ImageAnalysisAgent
from app.agents.orchestrator import run_pipeline
from app.agents.report_generator import ReportGenerationAgent
from app.agents.research import ResearchAgent
from app.agents.safety_monitor import SafetyAgent
from app.database import get_db
from app.models.report import Report
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.report import ReportResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

async def _get_user_report(
    report_id: UUID,
    user: User,
    db: AsyncSession,
) -> Report:
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == user.id,
        )
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return report


# ------------------------------------------------------------------
# Single report detail
# ------------------------------------------------------------------

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await _get_user_report(report_id, current_user, db)
    return ReportResponse.model_validate(report)


# ------------------------------------------------------------------
# Image analysis
# ------------------------------------------------------------------

@router.post("/{report_id}/analyze", response_model=ReportResponse)
async def analyze_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await _get_user_report(report_id, current_user, db)

    if not report.image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report has no uploaded image to analyze",
        )

    if report.status not in ("uploaded", "image_analyzed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report cannot be analyzed in its current status: {report.status}",
        )

    agent = ImageAnalysisAgent(db)
    try:
        report = await agent.analyze(report)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Image analysis failed for report %s: %s", report_id, e)
        report.status = "analysis_failed"
        await db.commit()
        await db.refresh(report)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Image analysis failed. Please try again later.",
        )

    return ReportResponse.model_validate(report)


# ------------------------------------------------------------------
# Research
# ------------------------------------------------------------------

@router.post("/{report_id}/research", response_model=ReportResponse)
async def research_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await _get_user_report(report_id, current_user, db)

    if not report.findings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report has no findings. Run image analysis first.",
        )

    if report.status not in ("image_analyzed", "research_complete"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report cannot be researched in its current status: {report.status}",
        )

    agent = ResearchAgent(db)
    try:
        report = await agent.research(report)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Research failed for report %s: %s", report_id, e)
        report.status = "research_failed"
        await db.commit()
        await db.refresh(report)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Research failed. Please try again later.",
        )

    return ReportResponse.model_validate(report)


# ------------------------------------------------------------------
# Report generation (single step)
# ------------------------------------------------------------------

@router.post("/{report_id}/generate-report", response_model=ReportResponse)
async def generate_report_only(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await _get_user_report(report_id, current_user, db)

    if not report.findings or not report.research_results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report needs both findings and research results. Run analysis and research first.",
        )

    if report.status not in ("research_complete", "report_generated"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report cannot be generated in its current status: {report.status}",
        )

    agent = ReportGenerationAgent(db)
    try:
        report = await agent.generate(report)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Report generation failed for %s: %s", report_id, e)
        report.status = "generation_failed"
        await db.commit()
        await db.refresh(report)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Report generation failed. Please try again later.",
        )

    return ReportResponse.model_validate(report)


# ------------------------------------------------------------------
# Safety review (single step)
# ------------------------------------------------------------------

@router.post("/{report_id}/safety-review", response_model=ReportResponse)
async def safety_review_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await _get_user_report(report_id, current_user, db)

    if not report.final_report:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report has no generated report. Run report generation first.",
        )

    if report.status not in ("report_generated", "complete"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report cannot be safety-reviewed in its current status: {report.status}",
        )

    agent = SafetyAgent(db)
    try:
        report = await agent.review(report)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Safety review failed for %s: %s", report_id, e)
        report.status = "safety_failed"
        await db.commit()
        await db.refresh(report)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Safety review failed. Please try again later.",
        )

    return ReportResponse.model_validate(report)


# ------------------------------------------------------------------
# Full pipeline: analyze → research → generate → safety review
# (orchestrated via LangGraph)
# ------------------------------------------------------------------

@router.post("/{report_id}/generate", response_model=ReportResponse)
async def generate_full_pipeline(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run the full report generation pipeline via LangGraph.

    Steps:
    1. Image analysis   (uploaded → image_analyzed)
    2. Research          (image_analyzed → research_complete)
    3. Report generation (research_complete → report_generated)
    4. Safety review     (report_generated → complete)

    Each step is skipped if the report has already passed that stage.
    If safety review fails, report generation is retried (max 2 times)
    with the safety feedback included in the prompt.
    """
    report = await _get_user_report(report_id, current_user, db)

    if not report.image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report has no uploaded image.",
        )

    try:
        result = await run_pipeline(report_id=str(report_id), db=db)
    except Exception as e:
        logger.error("Pipeline failed for report %s: %s", report_id, e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Pipeline failed: {e}",
        )

    await db.refresh(report)

    # No-findings is a valid terminal state
    if not result.get("has_findings", True) and report.status == "image_analyzed":
        return ReportResponse.model_validate(report)

    if report.status != "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pipeline could not complete. Report is in status: {report.status}",
        )

    return ReportResponse.model_validate(report)
