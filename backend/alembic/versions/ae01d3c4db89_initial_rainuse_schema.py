"""initial_rainuse_schema: PostGIS extension + all RainUSE tables from SQLAlchemy models.

Revision ID: ae01d3c4db89
Revises:
Create Date: 2026-04-11 16:02:31.531316

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "ae01d3c4db89"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable PostGIS, then create all tables from ``database.tables.Base`` metadata."""
    op.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))

    # Import side effects: registers models on Base.metadata.
    from database.tables import Base  # noqa: WPS433

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    """Drop all ORM tables (reverse of create_all)."""
    from database.tables import Base  # noqa: WPS433

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
