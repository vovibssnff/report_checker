"""datetime timezone

Revision ID: a1b2c3d4e5f6
Revises: 1d020c661350
Create Date: 2026-03-06

"""

from collections.abc import Sequence

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "1d020c661350"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE
        USING created_at AT TIME ZONE 'UTC'
        """
    )
    op.execute(
        """
        ALTER TABLE documents
        ALTER COLUMN uploaded_at TYPE TIMESTAMP WITH TIME ZONE
        USING uploaded_at AT TIME ZONE 'UTC'
        """
    )
    op.execute(
        """
        ALTER TABLE documents
        ALTER COLUMN checked_at TYPE TIMESTAMP WITH TIME ZONE
        USING checked_at AT TIME ZONE 'UTC'
        """
    )
    op.execute(
        """
        ALTER TABLE check_results
        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE
        USING created_at AT TIME ZONE 'UTC'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE
        USING created_at AT TIME ZONE 'UTC'
        """
    )
    op.execute(
        """
        ALTER TABLE documents
        ALTER COLUMN uploaded_at TYPE TIMESTAMP WITHOUT TIME ZONE
        USING uploaded_at AT TIME ZONE 'UTC'
        """
    )
    op.execute(
        """
        ALTER TABLE documents
        ALTER COLUMN checked_at TYPE TIMESTAMP WITHOUT TIME ZONE
        USING checked_at AT TIME ZONE 'UTC'
        """
    )
    op.execute(
        """
        ALTER TABLE check_results
        ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE
        USING created_at AT TIME ZONE 'UTC'
        """
    )
