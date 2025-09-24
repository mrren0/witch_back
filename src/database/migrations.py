"""Utilities for keeping the database schema up to date on application start."""

from __future__ import annotations

import fcntl
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.connection import Base, DATABASE_URL, engine
from src.database.models import TokenModel

from src.infra.logger import logger

# The workers started by Gunicorn are different processes.  We guard the
# migration execution with a file based lock so that only one of them performs
# the potentially expensive Alembic upgrade.  The other workers will wait for
# the lock and simply continue once the schema is up to date.
_LOCK_FILE = Path("/tmp/.alembic_migration.lock")
# The stamp file contains the latest Alembic revision that was applied.  We
# compare it with the current head to decide whether an upgrade is required.
_STAMP_FILE = Path("/tmp/.alembic_migration.stamp")

# Alembic needs a synchronous connection to introspect the currently applied
# revision.  The application itself talks to the database via ``asyncpg`` but
# for migration bookkeeping we open a lightweight synchronous engine using the
# same credentials.
_SYNC_DATABASE_URL = make_url(DATABASE_URL)
if "+asyncpg" in _SYNC_DATABASE_URL.drivername:
    _SYNC_DATABASE_URL = _SYNC_DATABASE_URL.set(
        drivername=_SYNC_DATABASE_URL.drivername.replace("+asyncpg", "+psycopg2")
    )
_SYNC_ENGINE = create_engine(_SYNC_DATABASE_URL)


def _get_current_database_revision() -> str | None:
    """Return the revision stored in the database or ``None`` if missing."""

    with _SYNC_ENGINE.connect() as connection:
        inspector = inspect(connection)
        if "alembic_version" not in inspector.get_table_names():
            return None

        result = connection.execute(text("SELECT version_num FROM alembic_version"))
        return result.scalar()


def ensure_schema_is_up_to_date() -> None:
    """Run Alembic migrations once per container start.

    The function is safe to be called multiple times – it is idempotent thanks
    to a combination of a file lock and a sentinel file.  If the migrations are
    already applied we simply return immediately.  Otherwise we execute
    ``alembic upgrade head`` to bring the database schema to the latest
    revision.
    """

    # Make sure the parent directory exists so that we can create the lock.
    _LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)

    with _LOCK_FILE.open("w") as lock_fp:
        fcntl.flock(lock_fp, fcntl.LOCK_EX)
        try:
            alembic_cfg = Config("alembic.ini")
            script_dir = ScriptDirectory.from_config(alembic_cfg)
                        try:
                current_head = script_dir.get_current_head()
                heads = [current_head]
            except Exception:
                # multiple heads or other script errors – fall back to all heads
                heads = list(script_dir.get_heads())
                current_head = ",".join(heads)

            stamped_revision = None
            if _STAMP_FILE.exists():
                stamped_revision = _STAMP_FILE.read_text().strip() or None

            database_revision = _get_current_database_revision()

            if database_revision == current_head:
                if stamped_revision != current_head:
                    _STAMP_FILE.write_text(current_head)
                logger.info(
                    "Database schema already at head revision %s – skipping upgrade",
                    current_head,
                )
                return

            if stamped_revision == current_head and database_revision != current_head:
                logger.warning(
                    "Stamp file recorded head revision %s but database is at %s – forcing upgrade",
                    stamped_revision,
                    database_revision or "<uninitialized>",
                )

            if stamped_revision is None and database_revision is None:
                logger.info(
                    "Applying database migrations up to head revision %s…",
                    current_head,
                )
            else:
                previous_revision = database_revision or stamped_revision
                logger.info(
                    "New migrations detected (%s → %s); applying upgrade…",
                    previous_revision,
                    current_head,
                )

            command.upgrade(alembic_cfg, "heads")
            _STAMP_FILE.write_text(current_head)
            logger.info(
                "Database migrations successfully applied – current revision %s",
                current_head,
            )
        finally:
            fcntl.flock(lock_fp, fcntl.LOCK_UN)


async def ensure_all_tables_exist() -> None:
    """Create any missing tables using the SQLAlchemy metadata."""

    try:
        async with engine.begin() as connection:  # type: AsyncConnection
            await connection.run_sync(Base.metadata.create_all)
            await connection.run_sync(_ensure_tokens_table_exists)
    except SQLAlchemyError as exc:
        logger.error("Failed to create database tables automatically: %s", exc)
        raise


def _ensure_tokens_table_exists(connection) -> None:
    """Create the ``tokens`` table if it is still missing.

    Under high parallel load with several Gunicorn workers starting at the
    same time we occasionally observed that the automatic metadata based table
    creation skipped the ``tokens`` table, leading to ``UndefinedTableError``
    once the application tried to query it.  The issue was hard to reproduce,
    but the safest fix is to explicitly verify the table presence after
    ``Base.metadata.create_all`` and create it manually when necessary.  The
    check is inexpensive and only runs during application start.
    """

    inspector = inspect(connection)
    if "tokens" not in inspector.get_table_names():
        logger.warning("Tokens table missing – creating it automatically")
        TokenModel.__table__.create(connection, checkfirst=True)
