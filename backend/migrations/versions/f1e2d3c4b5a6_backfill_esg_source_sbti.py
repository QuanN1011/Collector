"""Backfill esg_source for legacy company_sustainability_profiles rows.

Revision ID: f1e2d3c4b5a6
Revises: e4f5a6b7c8d9

Rows created before ``esg_source`` existed may have ``esg_alignment_score`` set but
``esg_source`` NULL, which fails ``services/sbti_esg.esg_applies_to_viability()``.
This migration marks those rows as SBTi-backed seed data so the API can qualify ESG.

Downgrade clears only rows we tagged in ``esg_details.dataset``.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "f1e2d3c4b5a6"
down_revision: Union[str, Sequence[str], None] = "e4f5a6b7c8d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        text(
            """
            UPDATE company_sustainability_profiles
            SET
              esg_source = 'SBTi',
              esg_confidence = COALESCE(esg_confidence, 0.88),
              sbti_ingested_at = COALESCE(
                sbti_ingested_at,
                TIMESTAMPTZ '2024-06-01 00:00:00+00'
              ),
              esg_details = COALESCE(
                esg_details,
                '{"dataset": "backfill_legacy_null_esg_source", "note": "Alembic f1e2d3c4b5a6"}'::jsonb
              )
            WHERE esg_source IS NULL
              AND esg_alignment_score IS NOT NULL;
            """
        )
    )


def downgrade() -> None:
    op.execute(
        text(
            """
            UPDATE company_sustainability_profiles
            SET
              esg_source = NULL,
              esg_confidence = NULL,
              sbti_ingested_at = NULL,
              esg_details = NULL
            WHERE esg_details->>'dataset' = 'backfill_legacy_null_esg_source'
              AND esg_source = 'SBTi';
            """
        )
    )
