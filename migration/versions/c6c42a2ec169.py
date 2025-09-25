"""Initial consolidated schema for witch.

Revision ID: c6c42a2ec169
Revises:
Create Date: 2025-09-25

This single revision creates the full schema currently used by the codebase.
Use on a clean dev DB, or run `alembic stamp base` first, then `alembic upgrade head`.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c6c42a2ec169"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("phone", sa.String(length=255), nullable=False, unique=True),
        sa.Column("coins", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("skin", sa.String(length=255), nullable=False, server_default=sa.text("''")),
        sa.Column("common_seed", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("epic_seed", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("rare_seed", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("water", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("level", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("booster", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("item", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("pot", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("last_update", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_users_phone", "users", ["phone"], unique=True)

    # products_item
    op.create_table(
        "products_item",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
    )

    # products
    op.create_table(
        "products",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("price", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("item_id", sa.Integer, sa.ForeignKey("products_item.id"), nullable=True),
    )

    # tokens
    op.create_table(
        "tokens",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("id_user", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_tokens_id_user", "tokens", ["id_user"], unique=False)
    op.create_index("ix_tokens_token", "tokens", ["token"], unique=True)

    # transactions
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("id_user", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("productId", sa.Integer, sa.ForeignKey("products.id"), nullable=False),
        sa.Column("purchaseId", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'in_progress'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_transactions_purchaseId", "transactions", ["purchaseId"], unique=True)

    # unadded_product
    op.create_table(
        "unadded_product",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("id_user", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("productId", sa.Integer, sa.ForeignKey("products.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # roulette_items
    op.create_table(
        "roulette_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("item", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("chance", sa.Float, nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_roulette_items_user_id", "roulette_items", ["user_id"], unique=False)

    # events
    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("logo", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("level_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # event_prizes
    op.create_table(
        "event_prizes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("events.id"), nullable=False, server_default=sa.text("-1")),
        sa.Column("place", sa.Integer, nullable=False),
        sa.Column("rewards", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )

    # event_ratings
    op.create_table(
        "event_ratings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("events.id"), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("result", sa.Float, nullable=False),
    )

    # event_history
    op.create_table(
        "event_history",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("events.id"), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("results", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )

    # unclaimed_rewards
    op.create_table(
        "unclaimed_rewards",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("events.id"), nullable=False),
        sa.Column("place", sa.Integer, nullable=False),
        sa.Column("rewards", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("user_id", "event_id", name="uq_reward_user_event"),
    )


def downgrade() -> None:
    op.drop_table("unclaimed_rewards")
    op.drop_table("event_history")
    op.drop_table("event_ratings")
    op.drop_table("event_prizes")
    op.drop_table("events")
    op.drop_index("ix_roulette_items_user_id", table_name="roulette_items")
    op.drop_table("roulette_items")
    op.drop_table("unadded_product")
    op.drop_index("ix_transactions_purchaseId", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_tokens_token", table_name="tokens")
    op.drop_index("ix_tokens_id_user", table_name="tokens")
    op.drop_table("tokens")
    op.drop_table("products")
    op.drop_table("products_item")
    op.drop_index("ix_users_phone", table_name="users")
    op.drop_table("users")
