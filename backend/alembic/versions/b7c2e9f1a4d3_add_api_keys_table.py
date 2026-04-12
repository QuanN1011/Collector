"""add api_keys table for Auth0-issued API keys.

Revision ID: b7c2e9f1a4d3
Revises: ae01d3c4db89
Create Date: 2026-04-12

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "b7c2e9f1a4d3"
down_revision: Union[str, Sequence[str], None] = "ae01d3c4db89"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if inspect(bind).has_table("api_keys"):
        return
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_sub", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=512), nullable=False),
        sa.Column("api_key", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_api_keys_user_sub"), "api_keys", ["user_sub"], unique=True)
    op.create_index(op.f("ix_api_keys_api_key"), "api_keys", ["api_key"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_api_keys_api_key"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_user_sub"), table_name="api_keys")
    op.drop_table("api_keys")
