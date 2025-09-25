"""DB schema bootstrap utilities: Alembic + SQLAlchemy metadata.

- Автомердж Alembic-веток при MultipleHeads
- Идемпотентный запуск (file-lock + stamp-файл)
- Фолбэк: досоздание таблиц из Base.metadata и явная проверка tokens

Безопасно для продакшена: merge-ревизии в Alembic не выполняют DDL, они только объединяют историю.
"""

from __future__ import annotations

import fcntl
from pathlib import Path
from typing import Sequence

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.util import CommandError
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from src.infra.logger import logger
from src.database.connection import engine, DATABASE_URL, Base
from src.database.models import TokenModel


# ─── Файлы-сентинелы для идемпотентности ──────────────────────────────────────
_LOCK_FILE = Path("/tmp/witch_alembic.lock")
_STAMP_FILE = Path("/tmp/witch_alembic.stamp")


# ─── Синхронный engine для Alembic ────────────────────────────────────────────
_SYNC_DATABASE_URL = make_url(DATABASE_URL)
if "+asyncpg" in _SYNC_DATABASE_URL.drivername:
    _SYNC_DATABASE_URL = _SYNC_DATABASE_URL.set(
        drivername=_SYNC_DATABASE_URL.drivername.replace("+asyncpg", "+psycopg2")
    )
_SYNC_ENGINE = create_engine(_SYNC_DATABASE_URL)


def _get_current_database_revision() -> str | None:
    """Вернуть ревизию из БД или ``None``, если версия не инициализирована."""
    with _SYNC_ENGINE.connect() as connection:
        inspector = inspect(connection)
        if "alembic_version" not in inspector.get_table_names():
            return None
        result = connection.execute(text("SELECT version_num FROM alembic_version"))
        return result.scalar()


def ensure_schema_is_up_to_date() -> None:
    """Обновить схему БД через Alembic один раз на старт контейнера.

    - Автослияние веток, если обнаружены multiple heads
    - Stamp-файл предотвращает повторные действия при параллельном старте
    """
    _LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)

    with _LOCK_FILE.open("w") as lock_fp:
        fcntl.flock(lock_fp, fcntl.LOCK_EX)
        try:
            alembic_cfg = Config("alembic.ini")
            script_dir = ScriptDirectory.from_config(alembic_cfg)

            # ── Проверка и авто-мёрдж голов ────────────────────────────────────
            try:
                current_head = script_dir.get_current_head()
            except CommandError as ce:
                # Alembic «The script directory has multiple heads»
                if "multiple heads" in str(ce).lower():
                    heads: Sequence[str] = script_dir.get_heads()
                    logger.warning("Alembic обнаружил несколько голов: %s — выполняю merge", heads)
                    # создаём merge-ревизию: без DDL; только объединение истории
                    command.merge(alembic_cfg, revisions=list(heads), message="auto-merge heads on startup")
                    # перечитываем новый head
                    script_dir = ScriptDirectory.from_config(alembic_cfg)
                    current_head = script_dir.get_current_head()
                    logger.info("Merge завершён, новый head: %s", current_head)
                else:
                    raise

            stamped_revision = None
            if _STAMP_FILE.exists():
                stamped_revision = (_STAMP_FILE.read_text().strip() or None)

            database_revision = _get_current_database_revision()

            if database_revision == current_head:
                if stamped_revision != current_head:
                    _STAMP_FILE.write_text(current_head)
                logger.info("Схема уже на head %s — пропускаю upgrade", current_head)
                return

            if stamped_revision == current_head and database_revision != current_head:
                logger.warning(
                    "В stamp-файле head=%s, но в БД=%s — принудительно обновляю",
                    stamped_revision, database_revision or "<uninitialized>",
                )

            # ── Апгрейд до head ────────────────────────────────────────────────
            if stamped_revision is None and database_revision is None:
                logger.info("Инициализация БД: применяю миграции до head %s…", current_head)
            else:
                prev = database_revision or stamped_revision
                logger.info("Обнаружены новые миграции (%s → %s); применяю upgrade…", prev, current_head)

            command.upgrade(alembic_cfg, "head")
            _STAMP_FILE.write_text(current_head)
            logger.info("Миграции применены, текущая ревизия: %s", current_head)

        finally:
            fcntl.flock(lock_fp, fcntl.LOCK_UN)


async def ensure_all_tables_exist() -> None:
    """Создать недостающие таблицы по SQLAlchemy metadata (идемпотентно)."""
    try:
        async with engine.begin() as connection:  # type: AsyncConnection
            await connection.run_sync(Base.metadata.create_all)
            await connection.run_sync(_ensure_tokens_table_exists)
    except SQLAlchemyError as exc:
        logger.error("Не удалось автоматически создать таблицы: %s", exc)
        raise


def _ensure_tokens_table_exists(connection) -> None:
    """Явно проверить/создать таблицу tokens (см. проблемы при гонках на старте)."""
    inspector = inspect(connection)
    if "tokens" not in inspector.get_table_names():
        logger.warning("Отсутствует tokens — создаю автоматически")
        TokenModel.__table__.create(connection, checkfirst=True)
