"""baseline schema aligned with current ORM models"""

from alembic import op
import sqlalchemy as sa

revision = "c6c42a2ec169"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("phone", sa.String(length=255), nullable=False, unique=True),
        sa.Column("coins", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column(
            "skin",
            sa.String(length=255),
            nullable=False,
            server_default=sa.text("'38ef8571-0e7d-4926-88db-fcb5a8892adb'"),
        ),
        sa.Column("common_seed", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("epic_seed", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("rare_seed", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("water", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("level", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("booster", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("item", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("pot", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_update",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_users_phone", "users", ["phone"], unique=True)

    op.create_table(
        "products_item",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("skin", sa.String(), nullable=False, server_default=sa.text("''")),
        sa.Column("coins", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("common_seed", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("epic_seed", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("rare_seed", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("water", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("level", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("booster", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("item", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("pot", sa.Integer, nullable=False, server_default=sa.text("0")),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("price", sa.Integer, nullable=False),
        sa.Column("id_product_item", sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(["id_product_item"], ["products_item.id"],),
    )

    op.create_table(
        "unadded_product",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("id_user", sa.Integer, nullable=False),
        sa.Column("productId", sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(["id_user"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["productId"], ["products.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "status",
            sa.String(length=255),
            nullable=False,
            server_default=sa.text("'unknown'"),
        ),
        sa.Column("productId", sa.Integer, nullable=False),
        sa.Column("id_user", sa.Integer, nullable=False),
        sa.Column(
            "purchaseId",
            sa.String(length=255),
            nullable=False,
            server_default=sa.text("''"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["productId"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["id_user"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_transactions_purchaseId", "transactions", ["purchaseId"], unique=False)

    op.create_table(
        "roulette_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("item", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("chance", sa.Float, nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_roulette_items_user_id", "roulette_items", ["user_id"], unique=False)

    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("logo", sa.String(length=255), nullable=False),
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
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "event_id", name="uq_reward_user_event"),
    )


def downgrade() -> None:
    op.drop_table("unclaimed_rewards")
    op.drop_table("event_ratings")
    op.drop_table("event_prizes")
    op.drop_table("event_history")
    op.drop_table("events")
    op.drop_index("ix_roulette_items_user_id", table_name="roulette_items")
    op.drop_table("roulette_items")
    op.drop_index("ix_transactions_purchaseId", table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("unadded_product")
    op.drop_table("products")
    op.drop_table("products_item")
    op.drop_index("ix_users_phone", table_name="users")
    op.drop_table("users")
