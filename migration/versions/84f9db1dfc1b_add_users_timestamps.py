"""Add missing users.created_at / users.last_update columns (idempotent).

Revision ID: 84f9db1dfc1b
Revises: c6c42a2ec169
Create Date: 2025-09-25

This migration adds the timestamp columns expected by the code during seeding.
It is idempotent and safe to run even if columns already exist.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "84f9db1dfc1b"
down_revision = "c6c42a2ec169"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='users' AND column_name='created_at'
          ) THEN
            ALTER TABLE users
              ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
          END IF;

          IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='users' AND column_name='last_update'
          ) THEN
            ALTER TABLE users
              ADD COLUMN last_update TIMESTAMPTZ NOT NULL DEFAULT NOW();
          END IF;

          -- backfill just in case
          UPDATE users SET created_at = NOW() WHERE created_at IS NULL;
          UPDATE users SET last_update = NOW() WHERE last_update IS NULL;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='users' AND column_name='last_update'
          ) THEN
            ALTER TABLE users DROP COLUMN last_update;
          END IF;

          IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='users' AND column_name='created_at'
          ) THEN
            ALTER TABLE users DROP COLUMN created_at;
          END IF;
        END $$;
        """
    )
