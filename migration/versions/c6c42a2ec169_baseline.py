"""baseline

Revision ID: c6c42a2ec169
Revises:
Create Date: 2025-07-25 10:23:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "c6c42a2ec169"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1️⃣ users ─ источник для всех ссылок «на пользователя»
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("login", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # 2️⃣ products-item ─ справочник ингредиентов/ресурсов
    op.create_table(
        "products-item",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("skin", sa.String(), server_default="", nullable=False),
        sa.Column("gold", sa.Integer, nullable=False),
        sa.Column("wood", sa.Integer, nullable=False),
        sa.Column("stone", sa.Integer, nullable=False),
        sa.Column("grass", sa.Integer, nullable=False),
        sa.Column("berry", sa.Integer, nullable=False),
        sa.Column("brick", sa.Integer, nullable=False),
        sa.Column("fish", sa.Integer, nullable=False),
        sa.Column("boards", sa.Integer, nullable=False),
        sa.Column("rope", sa.Integer, server_default="0", nullable=False),
    )

    # 3️⃣ products ─ сама таблица товаров + FK на products-item
    #    ▸ добавьте/замените поля под свою модель Product
    op.create_table(
        "products",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("id_product_item", sa.Integer, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(
            ["id_product_item"],
            ["products-item.id"],
            name="products_id_product_item_fkey",
        ),
    )

    # 4️⃣ unadded-product ─ хранит «не добавленные» товары пользователя
    op.create_table(
        "unadded-product",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("id_user", sa.Integer, nullable=False),
        sa.Column("productId", sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(
            ["id_user"], ["users.id"], name="unadded-product_id_user_fkey"
        ),
        sa.ForeignKeyConstraint(
            ["productId"], ["products.id"], name="unadded-product_productId_fkey"
        ),
    )

    # 5️⃣ events ─ события (уберите, если уже есть в другой ревизии)
    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
    )

    # 6️⃣ event_ratings ─ оценки событий
    op.create_table(
        "event_ratings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.Integer, nullable=False),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("result", sa.Float, nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("event_ratings")
    op.drop_table("events")
    op.drop_table("unadded-product")
    op.drop_table("products")
    op.drop_table("products-item")
    op.drop_table("users")
