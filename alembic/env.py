from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.db.base import metadata

# Alembic Config object, giving access to the values within alembic.ini.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model metadata used by `alembic revision --autogenerate`.
target_metadata = metadata

settings = get_settings()


def run_migrations_offline() -> None:
    """Emit migration SQL without a live DB connection (`alembic upgrade --sql`)."""
    context.configure(
        url=settings.database_url_async,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _run_migrations_sync(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations against a live DB using the app's async engine config."""
    connectable: AsyncEngine = create_async_engine(
        settings.database_url_async,
        connect_args=settings.database_connect_args,
        poolclass=NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(_run_migrations_sync)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
