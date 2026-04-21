"""
Alembic migration environment.

Usage:
  # Generate migration from model changes:
  alembic revision --autogenerate -m "add field X to posts"

  # Apply migrations:
  alembic upgrade head

  # Roll back one step:
  alembic downgrade -1

  # See current revision:
  alembic current

Why Alembic instead of Base.metadata.create_all():
  create_all() cannot ALTER existing tables — it only creates missing ones.
  Alembic generates proper ALTER TABLE / CREATE INDEX / DROP COLUMN SQL
  so schema changes are applied safely on every deploy without data loss.

  On Render, migrations run automatically on every deploy via render.yaml:
    buildCommand: pip install -r requirements.txt && alembic upgrade head
"""
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Load app models so Alembic can detect schema changes
from app.db.database import Base
from app.models import models  # noqa: F401

config = context.config

# Inject DATABASE_URL from environment — set automatically by Render
# when the PostgreSQL service is linked in render.yaml
config.set_main_option("DATABASE_URL", os.environ["DATABASE_URL"])

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL script)."""
    url = config.get_main_option("DATABASE_URL")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # NullPool for migrations — no persistent connections
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()