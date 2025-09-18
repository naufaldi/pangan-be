"""refine price scale and indexes

Revision ID: 78b4acd4c0a9
Revises: a66d9e35e77b
Create Date: 2025-09-01 14:01:52.228433

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '78b4acd4c0a9'
down_revision: Union[str, None] = 'a66d9e35e77b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use SQL to enforce price precision/scale and improve query performance
    op.execute(
        sa.text(
            """
            ALTER TABLE prices_monthly
            ALTER COLUMN price TYPE NUMERIC(14,2);

            -- Composite index to support common filter patterns
            CREATE INDEX IF NOT EXISTS idx_prices_monthly_level_period
              ON prices_monthly (level_harga_id, period_start DESC, period_end DESC);
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DROP INDEX IF EXISTS idx_prices_monthly_level_period;
            ALTER TABLE prices_monthly
            ALTER COLUMN price TYPE NUMERIC;
            """
        )
    )
