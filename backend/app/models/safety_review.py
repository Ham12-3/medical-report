import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SafetyReview(Base):
    __tablename__ = "safety_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False, unique=True, index=True
    )
    flagged_issues: Mapped[str | None] = mapped_column(Text, nullable=True)
    adjusted_confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommended_disclaimers: Mapped[str | None] = mapped_column(Text, nullable=True)
    safety_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    guardrail_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    report: Mapped["Report"] = relationship(back_populates="safety_review_record")
