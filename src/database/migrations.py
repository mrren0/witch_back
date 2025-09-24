"""Utilities for keeping the database schema up to date on application start."""

from __future__ import annotations

import fcntl
from pathlib import Path

from alembic import command
from alembic.config import Config

from src.infra.logger import logger

# The workers started by Gunicorn are different processes.  We guard the
# migration execution with a file based lock so that only one of them performs
# the potentially expensive Alembic upgrade.  The other workers will wait for
# the lock and simply continue once the schema is up to date.
_LOCK_FILE = Path("/tmp/.alembic_migration.lock")
_STAMP_FILE = Path("/tmp/.alembic_migration.stamp")


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
            if _STAMP_FILE.exists():
                logger.info("Database migrations already applied – skipping upgrade")
                return

            logger.info("Applying database migrations…")
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            _STAMP_FILE.write_text("applied")
            logger.info("Database migrations successfully applied")
        finally:
            fcntl.flock(lock_fp, fcntl.LOCK_UN)
