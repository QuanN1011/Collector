"""Add buildings CV snapshot columns (roof/tower inference persisted separately from catalog).

Revision ID: a3b4c5d6e7f8
Revises: f1e2d3c4b5a6

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, Sequence[str], None] = "f1e2d3c4b5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("buildings", sa.Column("roof_area_sqft_cv", sa.Float(), nullable=True))
    op.add_column("buildings", sa.Column("roof_area_confidence_cv", sa.Float(), nullable=True))
    op.add_column("buildings", sa.Column("cooling_tower_detected_cv", sa.Boolean(), nullable=True))
    op.add_column("buildings", sa.Column("cooling_tower_confidence_cv", sa.Float(), nullable=True))
    op.add_column(
        "buildings",
        sa.Column("cv_inference_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("buildings", sa.Column("cv_source", sa.String(length=64), nullable=True))
    op.add_column("buildings", sa.Column("cv_inference_model", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("buildings", "cv_inference_model")
    op.drop_column("buildings", "cv_source")
    op.drop_column("buildings", "cv_inference_at")
    op.drop_column("buildings", "cooling_tower_confidence_cv")
    op.drop_column("buildings", "cooling_tower_detected_cv")
    op.drop_column("buildings", "roof_area_confidence_cv")
    op.drop_column("buildings", "roof_area_sqft_cv")
