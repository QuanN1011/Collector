"""api_keys: unique index on email (one issued key per email).

Revision ID: d9e4f1a2b3c5
Revises: b7c2e9f1a4d3
Create Date: 2026-04-12

If ``upgrade`` fails due to duplicate emails in ``api_keys``, resolve rows manually then re-run.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect

revision: str = "d9e4f1a2b3c5"
down_revision: Union[str, Sequence[str], None] = "b7c2e9f1a4d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("api_keys"):
        return
    names = {ix["name"] for ix in insp.get_indexes("api_keys")}
    if "ix_api_keys_email" not in names:
        op.create_index("ix_api_keys_email", "api_keys", ["email"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if insp.has_table("api_keys"):
        names = {ix["name"] for ix in insp.get_indexes("api_keys")}
        if "ix_api_keys_email" in names:
            op.drop_index("ix_api_keys_email", table_name="api_keys")
