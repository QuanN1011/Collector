"""Alembic environment: uses DATABASE_URL and SQLAlchemy models in ``database.tables``."""

from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context

from env_load import load_backend_env

load_backend_env()

from database.tables import Base  # noqa: E402

import database.api_keys_dataset  # noqa: F401, E402 — register ApiKey on Base.metadata  # pyright: ignore[reportUnusedImport]

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Export it or create backend/.env (see backend/.env.example)."
        )
    return url


def run_migrations_offline() -> None:
    """Generate SQL without connecting (``alembic upgrade head --sql``)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(get_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
