"""add events + rename product tables, fix users.last_update

Revision ID: 83c91dec5c79
Revises: c6c42a2ec169
Create Date: 2025-07-28 17:19:35.475940
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ──────────────────────────────────────────────────────────────────────
revision: str = "83c91dec5c79"
down_revision: Union[str, None] = "c6c42a2ec169"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# ──────────────────────────────────────────────────────────────────────


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    table_names = inspector.get_table_names()

    if "products-item" in table_names and "products_item" not in table_names:
        op.rename_table("products-item", "products_item")

    if "unadded-product" in table_names and "unadded_product" not in table_names:
        op.rename_table("unadded-product", "unadded_product")

    if "products" in table_names:
        foreign_keys = inspector.get_foreign_keys("products")
        for fk in foreign_keys:
            if fk["referred_table"] == "products-item":
                op.drop_constraint(fk["name"], "products", type_="foreignkey")
                op.create_foreign_key(
                    "products_id_product_item_fkey",
                    "products",
                    "products_item",
                    ["id_product_item"],
                    ["id"],
                )
                break

    # ─── 2. last_update → NOT NULL (+ default + заполнение) ───────────
    # 2.0 Добавляем колонку только если её ещё нет
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_update TIMESTAMP WITH TIME ZONE"
    )
    # 2.1 Устанавливаем дефолт NOW()
    op.alter_column(
        "users",
        "last_update",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        server_default=sa.text("NOW()"),
    )
    # 2.2 Заполняем уже существующие NULL-ы
    op.execute("UPDATE users SET last_update = NOW() WHERE last_update IS NULL;")
    # 2.3 Ставим NOT NULL
    op.alter_column(
        "users",
        "last_update",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
    )

    # ─── 3. Новые таблицы для событий и наград ─────────────────────────
    # Предварительно убираем старые таблицы, чтобы избежать DuplicateTable
    op.execute("DROP TABLE IF EXISTS unclaimed_rewards CASCADE;")
    op.execute("DROP TABLE IF EXISTS event_ratings CASCADE;")
    op.execute("DROP TABLE IF EXISTS event_prizes CASCADE;")
    op.execute("DROP TABLE IF EXISTS event_history CASCADE;")
    op.execute("DROP TABLE IF EXISTS events CASCADE;")

    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("logo", sa.String(), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("level_ids", sa.JSON(), nullable=False),
    )

    op.create_table(
        "event_history",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.Integer, nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("results", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "event_prizes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.Integer, nullable=False),
        sa.Column("place", sa.Integer, nullable=False),
        sa.Column("rewards", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "event_ratings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.Integer, nullable=False),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("result", sa.Float, nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "unclaimed_rewards",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("event_id", sa.Integer, nullable=False),
        sa.Column("place", sa.Integer, nullable=False),
        sa.Column("rewards", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "event_id", name="uq_reward_user_event"),
    )


def downgrade() -> None:
    # ─── 1. Удаляем новые таблицы ─────────────────────────────────────
    op.drop_table("unclaimed_rewards")
    op.drop_table("event_ratings")
    op.drop_table("event_prizes")
    op.drop_table("event_history")
    op.drop_table("events")

    # ─── 2. last_update вернуть в исходное состояние ──────────────────
    op.alter_column(
        "users",
        "last_update",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        server_default=None,
        nullable=True,
    )

    # ─── 3. Возвращаем старые имена и FK ──────────────────────────────
    op.drop_constraint("products_id_product_item_fkey", "products", type_="foreignkey")
    op.create_foreign_key(
        "products_id_product_item_fkey",
        "products",
        "products-item",
        ["id_product_item"],
        ["id"],
    )

    op.rename_table("products_item", "products-item")
    op.rename_table("unadded_product", "unadded-product")
