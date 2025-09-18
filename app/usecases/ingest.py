from __future__ import annotations

import time
import logging
from calendar import monthrange
from datetime import date
from decimal import Decimal
from typing import Iterable, Mapping

from app.common.checksum import compute_price_checksum
from app.usecases.ports import (
    FetchParams,
    PriceRepositoryPort,
    PriceUpsertRow,
    UpsertSummary,
    UpstreamClientPort,
)
from app.usecases.schemas import NormalizedPriceRow, UpstreamPayload


MONTHS: dict[str, int] = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "Mei": 5,
    "Jun": 6,
    "Jul": 7,
    "Agu": 8,
    "Sep": 9,
    "Okt": 10,
    "Nov": 11,
    "Des": 12,
}


def _month_edges(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    end = date(year, month, monthrange(year, month)[1])
    return start, end


def _normalize_payload(*, payload: Mapping, params: FetchParams) -> list[NormalizedPriceRow]:
    validated = UpstreamPayload.model_validate(payload)
    rows: list[NormalizedPriceRow] = []
    buckets = validated.data
    for year_str, items in buckets.items():
        try:
            yr = int(year_str)
        except Exception:
            continue
        for it in items:
            unit = (it.today_province_price.satuan if it.today_province_price else "")
            commodity_id = str(it.commodity_id)
            for mk, mnum in MONTHS.items():
                mval = getattr(it, mk)
                if mval in (None, ""):
                    continue
                ps, pe = _month_edges(yr, mnum)
                if ps < params.period_start or pe > params.period_end:
                    # Keep only rows that intersect within requested window
                    continue
                price_val = Decimal(mval)
                row = NormalizedPriceRow(
                    commodity_id=commodity_id,
                    province_id="NATIONAL" if not params.province_id else str(params.province_id),
                    level_harga_id=params.level_harga_id,
                    period_start=ps,
                    period_end=pe,
                    price=price_val,
                    unit=unit,
                )
                rows.append(row)
    return rows


def _with_checksums(rows: Iterable[NormalizedPriceRow]) -> list[PriceUpsertRow]:
    out: list[PriceUpsertRow] = []
    for r in rows:
        checksum = compute_price_checksum(
            price=r.price,
            unit=r.unit,
            level_harga_id=r.level_harga_id,
            period_start=r.period_start,
            period_end=r.period_end,
            commodity_id=r.commodity_id,
        )
        out.append(
            PriceUpsertRow(
                commodity_id=r.commodity_id,
                province_id=r.province_id,
                level_harga_id=r.level_harga_id,
                period_start=r.period_start,
                period_end=r.period_end,
                price=r.price,
                unit=r.unit,
                checksum=checksum,
            )
        )
    return out


def fetch_and_upsert(*, client: UpstreamClientPort, repo: PriceRepositoryPort, params: FetchParams) -> UpsertSummary:
    logger = logging.getLogger(__name__)
    start_time = time.time()

    if params.start_year > params.end_year:
        raise ValueError("start_year must be <= end_year")
    if params.period_start > params.period_end:
        raise ValueError("period_start must be <= period_end")

    # Fetch phase
    fetch_start = time.time()
    payload = client.fetch(params)
    fetch_duration = time.time() - fetch_start

    # Normalize phase
    normalize_start = time.time()
    normalized = _normalize_payload(payload=payload, params=params)
    normalize_duration = time.time() - normalize_start

    # Checksum phase
    checksum_start = time.time()
    upsert_rows = _with_checksums(normalized)
    checksum_duration = time.time() - checksum_start

    # Upsert phase
    upsert_start = time.time()
    summary = repo.upsert_many(upsert_rows)
    upsert_duration = time.time() - upsert_start

    total_duration = time.time() - start_time

    # Structured logging
    logger.info(
        "Ingestion completed",
        extra={
            "operation": "ingest",
            "level_harga_id": params.level_harga_id,
            "province_id": params.province_id or "NATIONAL",
            "period_start": params.period_start.isoformat(),
            "period_end": params.period_end.isoformat(),
            "fetch_duration_ms": round(fetch_duration * 1000, 2),
            "normalize_duration_ms": round(normalize_duration * 1000, 2),
            "checksum_duration_ms": round(checksum_duration * 1000, 2),
            "upsert_duration_ms": round(upsert_duration * 1000, 2),
            "total_duration_ms": round(total_duration * 1000, 2),
            "normalized_rows": len(normalized),
            "upsert_rows": len(upsert_rows),
            "inserted": summary.inserted,
            "updated": summary.updated,
            "unchanged": summary.unchanged,
        }
    )

    return summary


