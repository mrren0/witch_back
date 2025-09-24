"""create tokens table for auth"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "2f4be8c4ef70"
down_revision: Union[str, None] = "83c91dec5c79"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "tokens" in inspector.get_table_names():
        return

    op.create_table(
        "tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("id_user", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["id_user"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token", name="uq_tokens_token"),
        sa.UniqueConstraint("id_user", name="uq_tokens_id_user"),
    )
    op.create_index("ix_tokens_id_user", "tokens", ["id_user"], unique=False)
    op.create_index("ix_tokens_token", "tokens", ["token"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "tokens" not in inspector.get_table_names():
        return

    op.drop_index("ix_tokens_token", table_name="tokens")
    op.drop_index("ix_tokens_id_user", table_name="tokens")
    op.drop_table("tokens")
