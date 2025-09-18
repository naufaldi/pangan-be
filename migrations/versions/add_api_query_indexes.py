"""add api query indexes

Revision ID: add_api_query_indexes
Revises: 78b4acd4c0a9
Create Date: 2025-09-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_api_query_indexes'
down_revision: Union[str, None] = '78b4acd4c0a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add indexes to optimize API query performance."""
    op.execute(
        sa.text(
            """
            -- Index for commodity filtering queries
            CREATE INDEX IF NOT EXISTS idx_prices_monthly_commodity
              ON prices_monthly (commodity_id);

            -- Index for province filtering queries
            CREATE INDEX IF NOT EXISTS idx_prices_monthly_province
              ON prices_monthly (province_id);

            -- Composite index for level + commodity filtering
            CREATE INDEX IF NOT EXISTS idx_prices_monthly_level_commodity
              ON prices_monthly (level_harga_id, commodity_id);

            -- Composite index for level + province filtering
            CREATE INDEX IF NOT EXISTS idx_prices_monthly_level_province
              ON prices_monthly (level_harga_id, province_id);

            -- Index for period range queries (complements existing level_period index)
            CREATE INDEX IF NOT EXISTS idx_prices_monthly_period_range
              ON prices_monthly (period_start, period_end)
              WHERE period_start IS NOT NULL AND period_end IS NOT NULL;
            """
        )
    )


def downgrade() -> None:
    """Remove API query performance indexes."""
    op.execute(
        sa.text(
            """
            DROP INDEX IF EXISTS idx_prices_monthly_commodity;
            DROP INDEX IF EXISTS idx_prices_monthly_province;
            DROP INDEX IF EXISTS idx_prices_monthly_level_commodity;
            DROP INDEX IF EXISTS idx_prices_monthly_level_province;
            DROP INDEX IF EXISTS idx_prices_monthly_period_range;
            """
        )
    )
