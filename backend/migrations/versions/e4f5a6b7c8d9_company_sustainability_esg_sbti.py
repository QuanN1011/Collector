"""company_sustainability_profiles: SBTi ESG provenance columns.

Revision ID: e4f5a6b7c8d9
Revises: d9e4f1a2b3c5
Create Date: 2026-04-12

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, Sequence[str], None] = "d9e4f1a2b3c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "company_sustainability_profiles",
        sa.Column("esg_source", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "company_sustainability_profiles",
        sa.Column("esg_confidence", sa.Float(), nullable=True),
    )
    op.add_column(
        "company_sustainability_profiles",
        sa.Column("sbti_ingested_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "company_sustainability_profiles",
        sa.Column("esg_details", JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("company_sustainability_profiles", "esg_details")
    op.drop_column("company_sustainability_profiles", "sbti_ingested_at")
    op.drop_column("company_sustainability_profiles", "esg_confidence")
    op.drop_column("company_sustainability_profiles", "esg_source")
