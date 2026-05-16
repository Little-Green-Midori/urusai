"""Alembic environment — async-aware, urusai settings-driven DSN."""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from urusai.config.settings import get_settings
from urusai.db.models import Base


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _build_dsn() -> str:
    s = get_settings()
    return (
        f"postgresql+asyncpg://{s.pg_user}:{s.pg_password}"
        f"@{s.pg_host}:{s.pg_port}/{s.pg_database}"
    )


def run_migrations_offline() -> None:
    context.configure(
        url=_build_dsn(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    cfg_section = config.get_section(config.config_ini_section, {}) or {}
    cfg_section["sqlalchemy.url"] = _build_dsn()
    connectable = async_engine_from_config(
        cfg_section, prefix="sqlalchemy.", future=True
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
