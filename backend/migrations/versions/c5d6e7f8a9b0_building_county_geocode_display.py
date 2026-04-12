"""Add county + Nominatim display_name to buildings.

Revision ID: c5d6e7f8a9b0
Revises: a3b4c5d6e7f8

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c5d6e7f8a9b0"
down_revision: Union[str, Sequence[str], None] = "a3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "buildings",
        sa.Column("county", sa.String(length=256), nullable=True),
    )
    op.add_column(
        "buildings",
        sa.Column("geocode_display_name", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("buildings", "geocode_display_name")
    op.drop_column("buildings", "county")
