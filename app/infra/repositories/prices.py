from __future__ import annotations

"""
SQLAlchemy-backed Price repository adapter (functional port).
"""

import logging
import time
from decimal import Decimal
from typing import Iterable, Sequence

from sqlalchemy import and_, desc, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.infra.models import PriceMonthly
from app.usecases.ports import (
    PaginatedPriceResult,
    PriceQuery,
    PriceRecord,
    PriceRepositoryPort,
    PriceUpsertRow,
    UpsertSummary,
)

logger = logging.getLogger(__name__)


def _to_record(row: PriceMonthly) -> PriceRecord:
    """Convert PriceMonthly with joined data to PriceRecord."""
    return PriceRecord(
        id=row.id,
        commodity_id=row.commodity_id,
        commodity_name=row.commodity.name,  # Access joined commodity data
        province_id=row.province_id,
        province_name=row.province.name,    # Access joined province data
        level_harga_id=row.level_harga_id,
        period_start=row.period_start,
        period_end=row.period_end,
        price=Decimal(str(row.price)),
        unit=row.unit,
    )


def make_price_repository(*, engine: Engine) -> PriceRepositoryPort:
    """Create a PriceRepositoryPort using the provided SQLAlchemy Engine."""

    def _find_existing(db: Session, r: PriceUpsertRow) -> PriceMonthly | None:
        stmt = select(PriceMonthly).where(
            and_(
                PriceMonthly.commodity_id == r.commodity_id,
                PriceMonthly.province_id == r.province_id,
                PriceMonthly.level_harga_id == r.level_harga_id,
                PriceMonthly.period_start == r.period_start,
                PriceMonthly.period_end == r.period_end,
            )
        )
        return db.execute(stmt).scalar_one_or_none()

    def upsert_many(rows: Iterable[PriceUpsertRow]) -> UpsertSummary:
        """Upsert multiple price records with error handling and logging."""
        start_time = time.time()
        items = list(rows)

        if not items:
            logger.debug("No items to upsert")
            return UpsertSummary(inserted=0, updated=0, unchanged=0)

        logger.info(
            "Starting batch upsert",
            extra={
                "batch_size": len(items),
                "sample_commodity": items[0].commodity_id if items else None,
                "sample_province": items[0].province_id if items else None,
            }
        )

        sql = text(
            """
            INSERT INTO prices_monthly (
                commodity_id, province_id, level_harga_id,
                period_start, period_end, price, unit, checksum
            ) VALUES (
                :commodity_id, :province_id, :level_harga_id,
                :period_start, :period_end, :price, :unit, :checksum
            )
            ON CONFLICT (commodity_id, province_id, level_harga_id, period_start, period_end)
            DO UPDATE SET
                price = EXCLUDED.price,
                unit = EXCLUDED.unit,
                checksum = EXCLUDED.checksum
            WHERE prices_monthly.checksum IS DISTINCT FROM EXCLUDED.checksum
            RETURNING (xmax = 0) AS inserted
            """
        )

        inserted = updated = unchanged = 0

        try:
            with engine.begin() as conn:
                for i, r in enumerate(items):
                    try:
                        params = {
                            "commodity_id": r.commodity_id,
                            "province_id": r.province_id,
                            "level_harga_id": r.level_harga_id,
                            "period_start": r.period_start,
                            "period_end": r.period_end,
                            "price": float(r.price),
                            "unit": r.unit,
                            "checksum": r.checksum,
                        }

                        res = conn.execute(sql, params)
                        row = res.fetchone()

                        if row is None:
                            # Conflict with identical checksum → DO NOTHING
                            unchanged += 1
                        else:
                            if bool(row.inserted):  # type: ignore[attr-defined]
                                inserted += 1
                            else:
                                updated += 1

                        # Log progress for large batches
                        if (i + 1) % 100 == 0:
                            logger.debug(
                                "Batch upsert progress",
                                extra={
                                    "processed": i + 1,
                                    "total": len(items),
                                    "inserted": inserted,
                                    "updated": updated,
                                    "unchanged": unchanged,
                                }
                            )

                    except Exception as e:
                        logger.error(
                            "Failed to upsert price record",
                            extra={
                                "error": str(e),
                                "record_index": i,
                                "commodity_id": r.commodity_id,
                                "province_id": r.province_id,
                                "period_start": r.period_start.isoformat(),
                                "period_end": r.period_end.isoformat(),
                            },
                            exc_info=True
                        )
                        # Continue processing other records instead of failing the whole batch
                        continue

            total_time = time.time() - start_time

            logger.info(
                "Batch upsert completed",
                extra={
                    "total_time_ms": round(total_time * 1000, 2),
                    "records_processed": len(items),
                    "inserted": inserted,
                    "updated": updated,
                    "unchanged": unchanged,
                    "success_rate": round((inserted + updated + unchanged) / len(items) * 100, 2),
                }
            )

            return UpsertSummary(inserted=inserted, updated=updated, unchanged=unchanged)

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(
                "Batch upsert failed",
                extra={
                    "error": str(e),
                    "total_time_ms": round(total_time * 1000, 2),
                    "records_attempted": len(items),
                    "inserted": inserted,
                    "updated": updated,
                    "unchanged": unchanged,
                },
                exc_info=True
            )
            raise

    def query(q: PriceQuery) -> PaginatedPriceResult:
        """Query prices with joins to include commodity and province names."""
        start_time = time.time()

        # Build filters
        filters = [PriceMonthly.level_harga_id == q.level_harga_id]
        if q.period_start:
            filters.append(PriceMonthly.period_start >= q.period_start)
        if q.period_end:
            filters.append(PriceMonthly.period_end <= q.period_end)
        if q.commodity_id:
            filters.append(PriceMonthly.commodity_id == q.commodity_id)
        if q.province_id:
            filters.append(PriceMonthly.province_id == q.province_id)

        from sqlalchemy import func
        from sqlalchemy.orm import joinedload

        try:
            with Session(bind=engine, future=True) as db:
                # Base query with joins to load related data
                base = (
                    select(PriceMonthly)
                    .options(
                        joinedload(PriceMonthly.commodity),
                        joinedload(PriceMonthly.province)
                    )
                    .where(and_(*filters))
                    .order_by(desc(PriceMonthly.period_start))
                )

                # Count query for total
                count_start = time.time()
                count_stmt = select(func.count()).select_from(
                    select(PriceMonthly.id).where(and_(*filters)).subquery()
                )
                total = db.execute(count_stmt).scalar_one()
                count_time = time.time() - count_start

                # Execute paginated query
                query_start = time.time()
                rows = (
                    db.execute(base.limit(q.limit).offset(q.offset)).scalars().all()
                )
                query_time = time.time() - query_start

                # Convert to PriceRecords
                conversion_start = time.time()
                records = [_to_record(r) for r in rows]
                conversion_time = time.time() - conversion_start

                total_time = time.time() - start_time

                # Log query performance
                logger.info(
                    "Price query completed",
                    extra={
                        "query_time_ms": round(total_time * 1000, 2),
                        "count_time_ms": round(count_time * 1000, 2),
                        "query_exec_time_ms": round(query_time * 1000, 2),
                        "conversion_time_ms": round(conversion_time * 1000, 2),
                        "record_count": len(records),
                        "total_count": int(total),
                        "limit": q.limit,
                        "offset": q.offset,
                        "level_harga_id": q.level_harga_id,
                        "commodity_id": q.commodity_id,
                        "province_id": q.province_id,
                        "period_start": q.period_start.isoformat() if q.period_start else None,
                        "period_end": q.period_end.isoformat() if q.period_end else None,
                    }
                )

                return PaginatedPriceResult(
                    data=records,
                    total=int(total),
                    limit=q.limit,
                    offset=q.offset
                )
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(
                "Price query failed",
                extra={
                    "error": str(e),
                    "query_time_ms": round(total_time * 1000, 2),
                    "level_harga_id": q.level_harga_id,
                    "limit": q.limit,
                    "offset": q.offset,
                },
                exc_info=True
            )
            raise

    return PriceRepositoryPort(upsert_many=upsert_many, query=query)
