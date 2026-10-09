"""
Alembic environment script.

Reads the database URL from Settings (environment variables) so that no
credentials are ever hardcoded. Uses the synchronous psycopg2 URL for
the Alembic CLI (online + offline modes).

To run migrations:
    alembic upgrade head
    alembic downgrade -1
    alembic revision --autogenerate -m "description"
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ─── Ensure the backend package is importable ─────────────────────────────────
# When Alembic runs from backend/, `app` is importable. When running from
# the repo root, we need to add backend/ to sys.path.
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(HERE)
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

# ─── Import settings ──────────────────────────────────────────────────────────
from app.core.config import get_settings  # noqa: E402

# ─── Import ALL models so their tables are registered with Base.metadata ──────
# This import triggers every model's __tablename__ to be registered.
# Do NOT import Base alone — import the full models package.
from app.models import Base  # noqa: E402 — also imports all models transitively
import app.models  # noqa: E402 — ensure __init__.py side-effects run

# ─── Alembic config ───────────────────────────────────────────────────────────
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Load the sync database URL from Settings
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url_sync)

target_metadata = Base.metadata


# ─── Offline mode (generate SQL without a live DB) ────────────────────────────
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ─── Online mode (connect to live DB and migrate) ─────────────────────────────
def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
