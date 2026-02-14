"""Create safety_reviews table

Revision ID: 002
Revises: 001
Create Date: 2025-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "safety_reviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "report_id",
            UUID(as_uuid=True),
            sa.ForeignKey("reports.id"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("flagged_issues", sa.Text, nullable=True),
        sa.Column("adjusted_confidence_score", sa.Float, nullable=True),
        sa.Column("recommended_disclaimers", sa.Text, nullable=True),
        sa.Column("safety_passed", sa.Boolean, server_default=sa.text("false")),
        sa.Column("guardrail_result", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("safety_reviews")
