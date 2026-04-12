"""add building_cv_analysis cache for Static Maps + Gemini live CV.

Revision ID: e3a1b2c4d5e6
Revises: d9e4f1a2b3c5
Create Date: 2026-04-11

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "e3a1b2c4d5e6"
down_revision: Union[str, Sequence[str], None] = "d9e4f1a2b3c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if inspect(bind).has_table("building_cv_analysis"):
        return
    op.create_table(
        "building_cv_analysis",
        sa.Column("building_id", sa.String(), sa.ForeignKey("buildings.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("roof_estimated_sqft", sa.Float(), nullable=False),
        sa.Column("roof_large_flag", sa.Boolean(), nullable=False),
        sa.Column("cooling_tower_detected", sa.Boolean(), nullable=False),
        sa.Column("roof_confidence", sa.Float(), nullable=False),
        sa.Column("cooling_tower_confidence", sa.Float(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("building_cv_analysis")
