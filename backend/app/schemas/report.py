from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ReportResponse(BaseModel):
    id: UUID
    user_id: UUID
    status: str
    image_url: Optional[str] = None
    findings: Optional[str] = None
    research_results: Optional[str] = None
    final_report: Optional[str] = None
    safety_review: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UploadResponse(BaseModel):
    id: UUID
    status: str
    image_url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SafetyReviewResponse(BaseModel):
    id: UUID
    report_id: UUID
    flagged_issues: Optional[str] = None
    adjusted_confidence_score: Optional[float] = None
    recommended_disclaimers: Optional[str] = None
    safety_passed: bool
    guardrail_result: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
