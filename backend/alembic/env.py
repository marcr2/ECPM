"""Alembic environment configuration for async migrations."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from ecpm.config import get_settings
from ecpm.models import Base

# Alembic Config object
config = context.config

# Set up loggers from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata

# Override sqlalchemy.url from application settings
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

# TimescaleDB internal objects to exclude from autogenerate
TIMESCALE_SCHEMAS = {"_timescaledb_catalog", "_timescaledb_internal", "_timescaledb_config"}
TIMESCALE_TABLE_PREFIXES = ("_hyper_", "_dist_hyper_", "compress_hyper_")


def include_object(
    obj: object,
    name: str | None,
    type_: str,
    reflected: bool,
    compare_to: object | None,
) -> bool:
    """Filter out TimescaleDB internal tables and indexes from autogenerate."""
    if type_ == "table" and name is not None:
        # Exclude TimescaleDB internal tables
        if any(name.startswith(prefix) for prefix in TIMESCALE_TABLE_PREFIXES):
            return False
    if type_ == "index" and name is not None:
        # Exclude TimescaleDB internal indexes
        if any(name.startswith(prefix) for prefix in TIMESCALE_TABLE_PREFIXES):
            return False
    if hasattr(obj, "schema") and getattr(obj, "schema", None) in TIMESCALE_SCHEMAS:
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):  # noqa: ANN001, ANN201
    """Execute migrations within a connection context."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode using asyncpg."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async engine."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
