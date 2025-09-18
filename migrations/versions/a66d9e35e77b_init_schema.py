"""init schema

Revision ID: a66d9e35e77b
Revises: 
Create Date: 2025-09-01 13:54:46.480251

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a66d9e35e77b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQL-first DDL for portability and explicit control
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS commodities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS provinces (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS prices_monthly (
                id BIGSERIAL PRIMARY KEY,
                commodity_id TEXT NOT NULL REFERENCES commodities(id),
                province_id TEXT NOT NULL REFERENCES provinces(id),
                level_harga_id INTEGER NOT NULL,
                period_start DATE NOT NULL,
                period_end DATE NOT NULL,
                price NUMERIC NOT NULL,
                unit TEXT NOT NULL,
                checksum TEXT,
                inserted_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ DEFAULT now(),
                CONSTRAINT ck_period_order CHECK (period_start <= period_end),
                CONSTRAINT uq_prices_monthly_unique_window UNIQUE (
                    commodity_id, province_id, level_harga_id, period_start, period_end
                )
            );

            -- Helpful indexes for common query patterns
            CREATE INDEX IF NOT EXISTS idx_prices_monthly_period_start
                ON prices_monthly (period_start DESC);
            CREATE INDEX IF NOT EXISTS idx_prices_monthly_filters
                ON prices_monthly (level_harga_id, period_start, period_end);
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DROP INDEX IF EXISTS idx_prices_monthly_filters;
            DROP INDEX IF EXISTS idx_prices_monthly_period_start;
            DROP TABLE IF EXISTS prices_monthly CASCADE;
            DROP TABLE IF EXISTS provinces CASCADE;
            DROP TABLE IF EXISTS commodities CASCADE;
            """
        )
    )
