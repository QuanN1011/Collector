"""add buildings.data_source for catchment lineage (priority 2).

Revision ID: b2f8a1c0d4e1
Revises: ae01d3c4db89
Create Date: 2026-04-12

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b2f8a1c0d4e1"
down_revision: Union[str, Sequence[str], None] = "ae01d3c4db89"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("buildings", sa.Column("data_source", sa.String(length=64), nullable=True))
    op.execute(
        "UPDATE buildings SET data_source = 'synthetic_commercial_seed' "
        "WHERE data_source IS NULL"
    )


def downgrade() -> None:
    op.drop_column("buildings", "data_source")
