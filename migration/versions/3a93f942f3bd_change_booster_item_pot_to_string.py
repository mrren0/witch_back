"""Change booster, item and pot columns to string.

Revision ID: 3a93f942f3bd
Revises: 84f9db1dfc1b
Create Date: 2025-09-25
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "3a93f942f3bd"
down_revision = "84f9db1dfc1b"
branch_labels = None
depends_on = None


_TARGET_TABLES = ("users", "products_item")
_TARGET_COLUMNS = ("booster", "item", "pot")


def upgrade() -> None:
    for table in _TARGET_TABLES:
        for column in _TARGET_COLUMNS:
            op.alter_column(
                table,
                column,
                type_=sa.String(),
                existing_type=sa.Integer(),
                existing_server_default=sa.text("0"),
                server_default=sa.text("''"),
                postgresql_using=f"{column}::text",
            )


def downgrade() -> None:
    for table in _TARGET_TABLES:
        for column in _TARGET_COLUMNS:
            op.alter_column(
                table,
                column,
                type_=sa.Integer(),
                existing_type=sa.String(),
                existing_server_default=sa.text("''"),
                server_default=sa.text("0"),
                postgresql_using=f"NULLIF({column}, '')::integer",
            )
